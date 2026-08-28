"""Knowledge Loader (docs/TECHNICAL-SPEC-V1.md §18).

Deterministic. Reads the human-owned ``knowledge/`` tree into an in-memory
``KnowledgeBundle``. A missing or malformed *required* file — any of the four
inventories, ``business-dna.md``, ``guardrails.yaml``, ``cluster-taxonomy.md`` —
is a hard failure (spec §3, §14): this raises ``KnowledgeError`` and the run must
abort before Signal Collection.

The opportunity registry is NOT required: a first run has none, and its absence
yields an empty ``registry`` (spec §3, §14).

This module never writes anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .io_utils import (
    LoadError,
    extract_yaml_blocks,
    read_yaml,
    read_yaml_front_matter,
)
from .schema.codec import CodecError, decode
from .schema.models import Guardrail, RunPaths
from .schema.validate import (
    InventoryIndex,
    ValidationError,
    blocking,
    validate_canonical_clusters,
    validate_guardrails,
)

_INVENTORY_SPECS = (
    ("artists", "artists", "artist_id"),
    ("playlists", "playlists", "playlist_id"),
    ("pages", "pages", "page_id"),
    ("catalog", "catalog", "catalog_id"),
)


class KnowledgeError(Exception):
    """A required knowledge file is missing or does not satisfy its structural rules."""


@dataclass(frozen=True)
class Cluster:
    id: str
    name: str


@dataclass
class KnowledgeBundle:
    project_root: Path
    paths: RunPaths
    business_dna_front_matter: dict
    business_dna_body: str
    content_methodology_body: Optional[str]
    guardrails: List[Guardrail]
    clusters: List[Cluster]
    inventory: InventoryIndex
    artists: list
    playlists: list
    pages: list
    catalog: list
    registry: list  # opportunity-registry entries; [] when the file is absent

    @property
    def canonical_cluster_ids(self) -> frozenset:
        return frozenset(c.id for c in self.clusters)


def load_knowledge(paths: RunPaths, *, project_root: Path) -> KnowledgeBundle:
    root = Path(project_root)

    def _p(rel: str) -> Path:
        return root / rel

    business_fm, business_body = _load_front_matter(_p(paths.business_dna_path), "business-dna.md")

    content_body: Optional[str] = None
    cm_path = _p(paths.content_methodology_path)
    if cm_path.exists():
        _, content_body = _load_front_matter(cm_path, "content-methodology.md")

    guardrails = _load_guardrails(_p(paths.guardrails_path))
    clusters = _load_clusters(_p(paths.taxonomy_path))
    artists, playlists, pages, catalog = _load_inventories(Path(paths.inventories_dir), root)
    inventory = _build_inventory_index(artists, playlists, pages, catalog)
    registry = _load_registry(_p(paths.registry_path))

    return KnowledgeBundle(
        project_root=root,
        paths=paths,
        business_dna_front_matter=business_fm,
        business_dna_body=business_body,
        content_methodology_body=content_body,
        guardrails=guardrails,
        clusters=clusters,
        inventory=inventory,
        artists=artists,
        playlists=playlists,
        pages=pages,
        catalog=catalog,
        registry=registry,
    )


# --- individual loaders -------------------------------------------------

def _fail(message: str, errors: Optional[List[ValidationError]] = None):
    if errors:
        message += ": " + "; ".join(f"{e.code} {e.message}" for e in errors)
    raise KnowledgeError(message)


def _load_front_matter(path: Path, label: str):
    if not path.exists():
        _fail(f"required knowledge file is missing: {label} ({path})")
    try:
        return read_yaml_front_matter(path)
    except LoadError as e:
        _fail(f"cannot load {label}: {e}")


def _load_guardrails(path: Path) -> List[Guardrail]:
    if not path.exists():
        _fail(f"required knowledge file is missing: guardrails.yaml ({path})")
    try:
        raw = read_yaml(path)
    except LoadError as e:
        _fail(f"cannot load guardrails.yaml: {e}")
    if not isinstance(raw, dict) or not isinstance(raw.get("guardrails"), list):
        _fail("guardrails.yaml must have a top-level 'guardrails' list")
    try:
        guardrails = [decode(Guardrail, g) for g in raw["guardrails"]]
    except CodecError as e:
        _fail(f"guardrails.yaml has a malformed entry: {e}")
    errs = blocking(validate_guardrails(guardrails))
    if errs:
        _fail("guardrails.yaml failed validation", errs)
    return guardrails


def _load_clusters(path: Path) -> List[Cluster]:
    if not path.exists():
        _fail(f"required knowledge file is missing: cluster-taxonomy.md ({path})")
    try:
        _, body = read_yaml_front_matter(path)
        blocks = extract_yaml_blocks(body)
    except LoadError as e:
        _fail(f"cannot load cluster-taxonomy.md: {e}")

    canonical = next(
        (b["canonical_clusters"] for b in blocks
         if isinstance(b, dict) and isinstance(b.get("canonical_clusters"), list)),
        None,
    )
    if canonical is None:
        _fail("cluster-taxonomy.md has no `canonical_clusters` YAML block")

    try:
        clusters = [Cluster(id=c["id"], name=c["name"]) for c in canonical]
    except (KeyError, TypeError) as e:
        _fail(f"cluster-taxonomy.md canonical_clusters entries need id + name: {e}")

    errs = blocking(validate_canonical_clusters([c.id for c in clusters]))
    if errs:
        _fail("cluster-taxonomy.md failed validation", errs)
    return clusters


def _load_inventories(inventories_dir: Path, root: Path):
    loaded = []
    for filename, key, id_field in _INVENTORY_SPECS:
        path = root / inventories_dir / f"{filename}.yaml"
        if not path.exists():
            _fail(f"required inventory file is missing: {filename}.yaml ({path})")
        try:
            raw = read_yaml(path)
        except LoadError as e:
            _fail(f"cannot load {filename}.yaml: {e}")
        records = raw.get(key) if isinstance(raw, dict) else None
        if not isinstance(records, list) or not records:
            _fail(f"{filename}.yaml must have a non-empty '{key}' list (spec §13)")
        for i, rec in enumerate(records):
            if not isinstance(rec, dict) or not rec.get(id_field):
                _fail(f"{filename}.yaml[{i}] is missing '{id_field}'")
        loaded.append(records)
    return tuple(loaded)


def _build_inventory_index(artists, playlists, pages, catalog) -> InventoryIndex:
    return InventoryIndex(
        artist_ids=frozenset(a["artist_id"] for a in artists),
        playlist_ids=frozenset(p["playlist_id"] for p in playlists),
        page_ids=frozenset(p["page_id"] for p in pages),
        catalog_ids=frozenset(c["catalog_id"] for c in catalog),
        own_page_ids=frozenset(p["page_id"] for p in pages if p.get("ownership") == "own"),
        reference_page_ids=frozenset(
            p["page_id"] for p in pages if p.get("ownership") == "reference_competitor"
        ),
    )


def _load_registry(path: Path) -> list:
    if not path.exists():
        return []
    try:
        raw = read_yaml(path)
    except LoadError as e:
        _fail(f"cannot load opportunity-registry.yaml: {e}")
    if raw is None:
        return []
    if isinstance(raw, dict):
        entries = raw.get("opportunities", [])
    elif isinstance(raw, list):
        entries = raw
    else:
        _fail("opportunity-registry.yaml must be a mapping with 'opportunities' or a list")
        entries = []
    if not isinstance(entries, list):
        _fail("opportunity-registry.yaml 'opportunities' must be a list")
    return entries
