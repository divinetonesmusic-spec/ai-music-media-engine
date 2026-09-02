"""Deterministic cluster-value normalisation (contract §3.1 step 1, §3.3).

Before Claude judges the cluster, a spelling / language / alias variant of an
existing canonical cluster is resolved to that canonical id. This is the guard
that stops artificial clusters: e.g. the Framing hypothesis
``limpieza-energetica (proposed_new)`` (Run 3 — a Spanish spelling) is the
existing canonical ``limpeza-energetica``.

No business decision is made here. The alias table covers (a) exact ids,
(b) case/whitespace, (c) slugified canonical display names in pt AND es,
(d) the one alias the taxonomy documents explicitly (``Sono Restaurador`` ->
``Sono``). Anything else returns ``None`` — Claude then re-tests it against the
11 clusters and, only if it genuinely fits none, produces a new-cluster proposal.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Union

from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.models import RunPaths

# Loaded once from the real taxonomy so the id set is never hard-coded twice.
_KB = load_knowledge(RunPaths(), project_root=Path(__file__).resolve().parents[2])
CANONICAL_IDS: FrozenSet[str] = frozenset(c.id for c in _KB.clusters)
_ID_TO_NAME: Dict[str, str] = {c.id: c.name for c in _KB.clusters}


def _slug(text: str) -> str:
    """ASCII, lowercase, non-alphanumerics -> single hyphen (accents folded)."""
    norm = unicodedata.normalize("NFKD", text)
    ascii_ = norm.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


# es display-name / slug -> canonical pt id. Curated for the 11 clusters only;
# every value is one of CANONICAL_IDS (asserted at import).
_ALIASES: Dict[str, str] = {
    # documented in cluster-taxonomy.md: Sono Restaurador is a subcluster of Sono
    "sono-restaurador": "sono",
    "sueno-reparador": "sono",
    "sueno-curativo": "sono",
    "musica-para-dormir": "sono",
    # es spellings of the canonical names
    "abundancia-prosperidad": "abundancia-prosperidade",
    "prosperidad": "abundancia-prosperidade",
    "limpieza-energetica": "limpeza-energetica",
    "limpeza-energetica": "limpeza-energetica",
    "frecuencia-divina-espiritualidad": "frequencia-divina-espiritualidade",
    "frecuencia-divina": "frequencia-divina-espiritualidade",
    "glandula-pineal-frecuencias": "glandula-pineal-frequencias",
    "glandula-pineal": "glandula-pineal-frequencias",
    "angeles-espiritualidad-religiosa": "anjos-espiritualidade-religiosa",
    "angeles": "anjos-espiritualidade-religiosa",
    "meditacion-relajacion": "meditacao-relaxamento",
    "meditacion": "meditacao-relaxamento",
    "ansiedad-relajacion": "ansiedade-relaxamento",
    "ansiedad": "ansiedade-relaxamento",
    "curacion-bienestar": "cura-bem-estar",
    "cura-bienestar": "cura-bem-estar",
    "enfoque-estudio": "foco-estudo",
    "foco-estudio": "foco-estudo",
    "sueno-lucido": "sonho-lucido",
    "sono-lucido": "sonho-lucido",
}
assert set(_ALIASES.values()) <= CANONICAL_IDS  # no alias points outside the taxonomy

# slug(canonical display name) -> id  (e.g. "frequencia-divina-espiritualidade")
_NAME_SLUGS: Dict[str, str] = {_slug(name): cid for cid, name in _ID_TO_NAME.items()}


def normalize_cluster_value(value: Optional[str], canonical_ids: FrozenSet[str]) -> Optional[str]:
    """Return the canonical cluster id for ``value``, or ``None`` if it matches none."""
    if not value or not value.strip():
        return None
    raw = value.strip()
    if raw in canonical_ids:
        return raw
    s = _slug(raw)
    if s in canonical_ids:
        return s
    if s in _NAME_SLUGS:
        return _NAME_SLUGS[s]
    if s in _ALIASES:
        return _ALIASES[s]
    return None


def load_taxonomy_markdown(project_root: Union[str, Path]) -> str:
    """The raw ``cluster-taxonomy.md`` text — passed to the strategy prompt so
    Claude reasons about each cluster's stated conceptual boundary (contract §3.1)."""
    path = Path(project_root) / RunPaths().taxonomy_path
    return path.read_text(encoding="utf-8")
