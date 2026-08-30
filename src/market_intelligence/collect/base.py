"""Common infrastructure for Signal Collection (spec §6.7, §18).

Nothing here is source-specific. A concrete collector (e.g. ``InternalDataCollector``)
supplies raw records and a record -> ``Signal`` mapping; this module owns
``signal_id`` allocation, raw-capture persistence, replay routing, and the
per-source degrade / all-sources hard-fail policy (§14).
"""

from __future__ import annotations

import abc
import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional

from ..io_utils import LoadError, read_json
from ..schema.enums import CaptureMethod, SourceType
from ..schema.ids import signal_id as _signal_id
from ..schema.models import RunConfig, Signal


def iso_utc(moment: _dt.datetime) -> str:
    """ISO 8601 in UTC with a trailing ``Z`` (spec uses this for collected_at / captured_at)."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=_dt.timezone.utc)
    return moment.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def raw_ref_for(run_id: str, signal_id: str) -> str:
    """The ``Signal.raw_ref`` value — always the literal ``data/`` prefix (spec §6.1, §6.3).

    If ``RunConfig.paths.data_dir`` is customised, the raw file still lives under that
    directory on disk; only this reference string is fixed by the spec.
    """
    return f"data/{run_id}/signals/raw/{signal_id}.json"


class SignalIdAllocator:
    """Per-run monotonic counter -> ``sig_<run_id>_<NNNN>`` (spec §6.1 TECHNICAL DEFAULT)."""

    def __init__(self, run_id: str, start: int = 1):
        self._run_id = run_id
        self._next = start

    def allocate(self) -> str:
        sid = _signal_id(self._run_id, self._next)
        self._next += 1
        return sid

    @property
    def count(self) -> int:
        return self._next - 1


@dataclass
class RawCapture:
    """One raw capture file (spec §6.7). ``raw_content`` must be JSON-serialisable."""

    signal_id: str
    source_type: SourceType
    capture_method: CaptureMethod
    query_or_reference: str
    captured_at: str  # ISO 8601 datetime
    raw_content: Any  # opaque text or JSON — enough to re-derive the Signal and to replay
    url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "source_type": self.source_type.value,
            "capture_method": self.capture_method.value,
            "query_or_reference": self.query_or_reference,
            "url": self.url,
            "captured_at": self.captured_at,
            "raw_content": self.raw_content,
        }


class RawCaptureStore:
    """Reads / writes ``data/<run_id>/signals/raw/<signal_id>.json`` (spec §6.7)."""

    def __init__(self, raw_dir: Path):
        self.raw_dir = Path(raw_dir)

    def _path(self, signal_id: str) -> Path:
        return self.raw_dir / f"{signal_id}.json"

    def write(self, capture: RawCapture) -> Path:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        path = self._path(capture.signal_id)
        # json.dumps raises TypeError on non-serialisable content before any file write.
        text = json.dumps(capture.to_dict(), ensure_ascii=False, indent=2, sort_keys=False)
        path.write_text(text, encoding="utf-8")
        return path

    def copy_from(self, source: Path) -> Path:
        raw = read_json(source)
        if not isinstance(raw, dict) or "signal_id" not in raw:
            raise LoadError(f"fixture raw capture {source} has no signal_id")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        dst = self._path(raw["signal_id"])
        dst.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        return dst

    def read_all(self) -> List[dict]:
        if not self.raw_dir.is_dir():
            return []
        return [read_json(p) for p in sorted(self.raw_dir.glob("*.json"))]

    def exists(self, signal_id: str) -> bool:
        return self._path(signal_id).is_file()


# --- collector interface ---------------------------------------------------

@dataclass
class SignalCollectionContext:
    """Everything a collector needs, plus the run's shared id allocator and raw store."""

    config: RunConfig
    project_root: Path
    now: Callable[[], _dt.datetime]
    allocator: SignalIdAllocator
    store: RawCaptureStore

    @property
    def run_id(self) -> str:
        return self.config.run_id

    @property
    def replay(self) -> bool:
        return bool(self.config.replay.enabled)

    @property
    def replay_llm_mode(self) -> str:
        """``"recorded"`` (default) or ``"live"`` (spec §22)."""
        return self.config.replay.llm or "recorded"

    @property
    def fixture_path(self) -> Optional[Path]:
        """The resolved ``replay.fixture_path`` base directory (§22)."""
        fp = self.config.replay.fixture_path
        if not fp:
            return None
        base = Path(fp)
        return base if base.is_absolute() else self.project_root / base

    @property
    def fixture_raw_dir(self) -> Optional[Path]:
        base = self.fixture_path
        return None if base is None else base / "signals" / "raw"

    def iso_now(self) -> str:
        return iso_utc(self.now())


class CollectorError(Exception):
    """A collector could not run at all (bad input file, missing config). Degradable (§14)."""


class Collector(abc.ABC):
    """A source-specific collector. The base pipeline handles ids, raw files and replay."""

    source_type: ClassVar[SourceType]
    capture_method: ClassVar[CaptureMethod]

    #: When True, ``live_records`` is called even in replay mode — the collector
    #: sources its own recorded fixtures (e.g. an LLM-dependent collector reading
    #: ``<fixture_path>/llm/<stage>/<key>.json``, spec §22). When False (default),
    #: replay rebuilds this source's signals from ``signals/raw/*.json``.
    replay_uses_live_path: ClassVar[bool] = False

    @abc.abstractmethod
    def live_records(self, ctx: SignalCollectionContext) -> List[dict]:
        """Fetch / read the source and return raw records (each JSON-serialisable).

        Raise ``CollectorError`` if the source is unavailable — the run degrades (§14).
        """

    @abc.abstractmethod
    def record_to_signal(
        self,
        record: dict,
        *,
        signal_id: str,
        collected_at: str,
        query_or_reference: str,
        ctx: SignalCollectionContext,
    ) -> Signal:
        """Map a raw record (+ id, capture time, provenance reference) to a ``Signal``."""

    def query_or_reference(
        self, record: dict, index: int, ctx: SignalCollectionContext
    ) -> str:
        """Provenance.query_or_reference for a record (spec §16.1). Overridable."""
        return f"{self.source_type.value} record {index}"

    def record_url(self, record: dict) -> Optional[str]:
        """Optional canonical URL for a record's raw capture."""
        return None


# --- collection result ---------------------------------------------------

@dataclass
class CollectorOutcome:
    source_type: SourceType
    ok: bool
    signal_count: int = 0
    failure_reason: Optional[str] = None


@dataclass
class CollectionResult:
    signals: List[Signal]
    outcomes: List[CollectorOutcome]
    replay: bool

    @property
    def sources_used(self) -> List[str]:
        return [o.source_type.value for o in self.outcomes if o.ok]

    @property
    def sources_failed(self) -> List[dict]:
        return [
            {"source": o.source_type.value, "reason": o.failure_reason}
            for o in self.outcomes
            if not o.ok
        ]


class SignalCollectionError(Exception):
    """Every configured signal source failed — the run must abort (§14)."""


# --- orchestration ---------------------------------------------------

def _default_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def make_context(
    config: RunConfig,
    *,
    project_root: Path,
    now: Optional[Callable[[], _dt.datetime]] = None,
) -> SignalCollectionContext:
    root = Path(project_root)
    raw_dir = root / config.paths.data_dir / config.run_id / "signals" / "raw"
    return SignalCollectionContext(
        config=config,
        project_root=root,
        now=now or _default_now,
        allocator=SignalIdAllocator(config.run_id),
        store=RawCaptureStore(raw_dir),
    )


def collect_signals(
    config: RunConfig,
    *,
    project_root: Path,
    collectors: Optional[Dict[SourceType, Collector]] = None,
    now: Optional[Callable[[], _dt.datetime]] = None,
) -> CollectionResult:
    """Run every collector named in ``config.signal_sources`` and aggregate.

    Degrades per source (§14); raises ``SignalCollectionError`` only if *all*
    configured sources fail. In replay mode the live sources are not contacted.
    """
    registry = DEFAULT_COLLECTORS if collectors is None else collectors
    ctx = make_context(config, project_root=project_root, now=now)

    signals: List[Signal] = []
    outcomes: List[CollectorOutcome] = []

    replay_records = _load_replay_records(ctx) if ctx.replay else {}

    for source_type in config.signal_sources:
        collector = registry.get(source_type)
        if collector is None:
            outcomes.append(CollectorOutcome(
                source_type=source_type,
                ok=False,
                failure_reason="collector not implemented yet",
            ))
            continue
        try:
            if not ctx.replay or collector.replay_uses_live_path:
                produced = _collect_live(collector, ctx)
            elif source_type in replay_records:
                produced = _collect_replay(collector, replay_records, ctx)
            else:
                # Reference the config value as written (relative/portable), not the
                # machine-resolved absolute path — the manifest must stay reproducible.
                outcomes.append(CollectorOutcome(
                    source_type=source_type, ok=False,
                    failure_reason=(
                        f"no replay fixtures for {source_type.value} under "
                        f"{config.replay.fixture_path}/signals/raw/"
                    ),
                ))
                continue
        except CollectorError as e:
            outcomes.append(CollectorOutcome(
                source_type=source_type, ok=False, failure_reason=str(e),
            ))
            continue
        signals.extend(produced)
        outcomes.append(CollectorOutcome(
            source_type=source_type, ok=True, signal_count=len(produced),
        ))

    if outcomes and not any(o.ok for o in outcomes):
        reasons = "; ".join(f"{o.source_type.value}: {o.failure_reason}" for o in outcomes)
        raise SignalCollectionError(f"every configured signal source failed — {reasons}")

    return CollectionResult(signals=signals, outcomes=outcomes, replay=ctx.replay)


def _collect_live(collector: Collector, ctx: SignalCollectionContext) -> List[Signal]:
    records = collector.live_records(ctx)
    out: List[Signal] = []
    for i, record in enumerate(records):
        sid = ctx.allocator.allocate()
        collected_at = ctx.iso_now()
        qor = collector.query_or_reference(record, i, ctx)
        ctx.store.write(RawCapture(
            signal_id=sid,
            source_type=collector.source_type,
            capture_method=collector.capture_method,
            query_or_reference=qor,
            captured_at=collected_at,
            raw_content=record,
            url=collector.record_url(record),
        ))
        out.append(collector.record_to_signal(
            record, signal_id=sid, collected_at=collected_at,
            query_or_reference=qor, ctx=ctx,
        ))
    return out


def _load_replay_records(ctx: SignalCollectionContext) -> Dict[SourceType, List[dict]]:
    """Group ``<fixture_path>/signals/raw/*.json`` by source_type (spec §22).

    Returns ``{}`` when the directory is absent — a collector with no fixtures is
    then reported as a per-source failure by ``collect_signals`` (which becomes a
    hard failure only if every source fails, §14).
    """
    fixture_raw = ctx.fixture_raw_dir
    if fixture_raw is None or not fixture_raw.is_dir():
        return {}
    grouped: Dict[SourceType, List[dict]] = {}
    for path in sorted(fixture_raw.glob("*.json")):
        raw = read_json(path)
        try:
            st = SourceType(raw["source_type"])
        except (KeyError, ValueError) as e:
            raise SignalCollectionError(f"fixture {path} has a bad source_type: {e}") from e
        grouped.setdefault(st, []).append(raw)
    return grouped


def _collect_replay(
    collector: Collector,
    grouped: Dict[SourceType, List[dict]],
    ctx: SignalCollectionContext,
) -> List[Signal]:
    out: List[Signal] = []
    for raw in grouped.get(collector.source_type, []):
        sid = raw["signal_id"]
        collected_at = raw.get("captured_at") or ctx.iso_now()
        qor = raw.get("query_or_reference", "")
        # Make the run's data dir self-contained: raw_ref must resolve there (§6.3).
        ctx.store.write(RawCapture(
            signal_id=sid,
            source_type=collector.source_type,
            capture_method=collector.capture_method,
            query_or_reference=qor,
            captured_at=collected_at,
            raw_content=raw.get("raw_content"),
            url=raw.get("url"),
        ))
        out.append(collector.record_to_signal(
            raw.get("raw_content"), signal_id=sid, collected_at=collected_at,
            query_or_reference=qor, ctx=ctx,
        ))
    return out


# Populated at import time from the modules in this package.
DEFAULT_COLLECTORS: Dict[SourceType, Collector] = {}


def register_default(collector: Collector) -> Collector:
    DEFAULT_COLLECTORS[collector.source_type] = collector
    return collector
