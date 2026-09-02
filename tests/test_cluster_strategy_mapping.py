"""Cluster Strategy V1 — deterministic cluster normalisation (contract §3.1, §3.3).

The anti-artificial-cluster guard: a spelling / language / alias variant of an
existing canonical cluster is mapped to that cluster BEFORE any Claude judgement,
so 'limpieza-energetica' (es) is never treated as a new cluster.
"""

from __future__ import annotations

import pytest
from tests.conftest import PROJECT_ROOT

from cluster_strategy.mapping import (
    CANONICAL_IDS,
    load_taxonomy_markdown,
    normalize_cluster_value,
)


def test_the_11_canonical_ids_are_loaded_from_the_taxonomy():
    assert CANONICAL_IDS == frozenset({
        "sono", "abundancia-prosperidade", "limpeza-energetica",
        "frequencia-divina-espiritualidade", "glandula-pineal-frequencias",
        "anjos-espiritualidade-religiosa", "meditacao-relaxamento",
        "ansiedade-relaxamento", "cura-bem-estar", "foco-estudo", "sonho-lucido",
    })


@pytest.mark.parametrize("value,expected", [
    ("limpeza-energetica", "limpeza-energetica"),          # exact
    ("  Limpeza-Energetica  ", "limpeza-energetica"),      # case + whitespace
    ("limpieza-energetica", "limpeza-energetica"),         # es spelling (the Run 3 case)
    ("Limpieza Energética", "limpeza-energetica"),         # es display name
    ("Limpeza Energética", "limpeza-energetica"),          # pt display name
    ("Sono Restaurador", "sono"),                          # documented subcluster -> root
    ("sono-restaurador", "sono"),
    ("Sueño Lúcido", "sonho-lucido"),                      # es
    ("meditacion-relajacion", "meditacao-relaxamento"),    # es
    ("Foco / Estudo", "foco-estudo"),
])
def test_normalises_spelling_and_language_variants_to_a_canonical_id(value, expected):
    assert normalize_cluster_value(value, CANONICAL_IDS) == expected


@pytest.mark.parametrize("value", [
    "night-overthinking-reset",      # a genuinely novel theme
    "commute-decompression",
    "",
    "   ",
])
def test_a_genuinely_novel_theme_does_not_map_to_any_canonical_cluster(value):
    assert normalize_cluster_value(value, CANONICAL_IDS) is None


def test_taxonomy_markdown_is_available_for_the_prompt():
    body = load_taxonomy_markdown(PROJECT_ROOT)
    assert "Fronteira conceitual" in body          # the per-cluster boundary prose
    assert "canonical_cluster_count: 11" in body
    assert "Sono Restaurador" in body
