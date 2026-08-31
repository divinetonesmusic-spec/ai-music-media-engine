"""Knowledge Loader (spec §18) — loads the real knowledge/ tree; hard-fails on
any missing or malformed required file (spec §3, §14)."""

from __future__ import annotations

import textwrap

import pytest
import yaml

from market_intelligence.knowledge_loader import KnowledgeError, load_knowledge
from market_intelligence.schema.models import RunPaths

# --- against the real repo -------------------------------------------------

def test_loads_the_real_knowledge_tree(project_root):
    kb = load_knowledge(RunPaths(), project_root=project_root)

    assert [g.guardrail_id for g in kb.guardrails] == [f"G{i:02d}" for i in range(1, 11)]
    assert len(kb.clusters) == 11
    assert "sono" in kb.canonical_cluster_ids

    assert len(kb.artists) == 37
    assert len(kb.playlists) == 8
    assert len(kb.pages) == 49
    assert len(kb.catalog) == 133
    assert len(kb.inventory.own_page_ids) == 5
    assert len(kb.inventory.reference_page_ids) == 44
    assert "art_5NJXbvpRnlTAqZ5neNTWGT" in kb.inventory.artist_ids
    assert "pl_5Wz1PL0H0t7f1qCuY989ZE" in kb.inventory.playlist_ids


def test_an_absent_registry_loads_as_an_empty_list_not_an_error(project_root):
    # the real knowledge tree, but pointed at a registry path that does not exist
    # (a first-ever run, or a fresh clone) — must load cleanly as [].
    kb = load_knowledge(
        RunPaths(registry_path="knowledge/market/_no_such_registry_.yaml"),
        project_root=project_root,
    )
    assert kb.registry == []


def test_business_dna_front_matter_is_parsed(project_root):
    kb = load_knowledge(RunPaths(), project_root=project_root)
    assert kb.business_dna_front_matter.get("title", "").startswith("Business DNA")
    assert kb.content_methodology_body is not None


# --- synthetic tree: negative cases --------------------------------------

@pytest.fixture
def fake_knowledge(tmp_path):
    """A minimal but complete knowledge tree the loader accepts."""
    root = tmp_path
    (root / "knowledge/business-dna").mkdir(parents=True)
    (root / "knowledge/rules").mkdir(parents=True)
    (root / "knowledge/clusters").mkdir(parents=True)
    (root / "knowledge/inventories").mkdir(parents=True)
    (root / "knowledge/market").mkdir(parents=True)

    (root / "knowledge/business-dna/business-dna.md").write_text(
        "---\ntitle: Business DNA — test\n---\n\n# body\n", encoding="utf-8"
    )
    (root / "knowledge/business-dna/content-methodology.md").write_text(
        "# Content methodology\n", encoding="utf-8"
    )

    guardrails = {
        "meta": {"schema_version": "1.0.0"},
        "guardrails": [
            {
                "guardrail_id": f"G{i:02d}",
                "name": f"g{i}",
                "type": "prohibition",
                "description": "x",
                "severity": "HIGH",
                "action_on_violation": "flag",
            }
            for i in range(1, 11)
        ],
    }
    (root / "knowledge/rules/guardrails.yaml").write_text(
        yaml.safe_dump(guardrails), encoding="utf-8"
    )

    cluster_ids = [f"c{i}" for i in range(1, 12)]
    taxonomy_md = "---\ntitle: taxonomy\n---\n\n```yaml\ncanonical_clusters:\n" + "".join(
        f'  - id: {cid}\n    name: "{cid}"\n' for cid in cluster_ids
    ) + "```\n"
    (root / "knowledge/clusters/cluster-taxonomy.md").write_text(taxonomy_md, encoding="utf-8")

    for name, key, rows in [
        ("artists", "artists", [{"artist_id": "art_1", "ownership": "own"}]),
        ("playlists", "playlists", [{"playlist_id": "pl_1"}]),
        (
            "pages",
            "pages",
            [
                {"page_id": "page_own_1", "ownership": "own"},
                {"page_id": "page_ref_1", "ownership": "reference_competitor"},
            ],
        ),
        ("catalog", "catalog", [{"catalog_id": "cat_1", "artist_id": "art_1"}]),
    ]:
        (root / f"knowledge/inventories/{name}.yaml").write_text(
            yaml.safe_dump({"meta": {}, key: rows}), encoding="utf-8"
        )

    return root


def test_synthetic_tree_loads(fake_knowledge):
    kb = load_knowledge(RunPaths(), project_root=fake_knowledge)
    assert len(kb.clusters) == 11
    assert kb.inventory.own_page_ids == frozenset({"page_own_1"})
    assert kb.inventory.reference_page_ids == frozenset({"page_ref_1"})


def test_missing_required_file_is_a_hard_failure(fake_knowledge):
    (fake_knowledge / "knowledge/rules/guardrails.yaml").unlink()
    with pytest.raises(KnowledgeError) as ei:
        load_knowledge(RunPaths(), project_root=fake_knowledge)
    assert "guardrails.yaml" in str(ei.value)


def test_wrong_guardrail_count_is_a_hard_failure(fake_knowledge):
    path = fake_knowledge / "knowledge/rules/guardrails.yaml"
    data = yaml.safe_load(path.read_text())
    data["guardrails"] = data["guardrails"][:8]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(KnowledgeError):
        load_knowledge(RunPaths(), project_root=fake_knowledge)


def test_wrong_cluster_count_is_a_hard_failure(fake_knowledge):
    path = fake_knowledge / "knowledge/clusters/cluster-taxonomy.md"
    md = path.read_text().replace("  - id: c11\n    name: \"c11\"\n", "")
    path.write_text(md, encoding="utf-8")
    with pytest.raises(KnowledgeError):
        load_knowledge(RunPaths(), project_root=fake_knowledge)


def test_empty_inventory_list_is_a_hard_failure(fake_knowledge):
    (fake_knowledge / "knowledge/inventories/playlists.yaml").write_text(
        "meta: {}\nplaylists: []\n", encoding="utf-8"
    )
    with pytest.raises(KnowledgeError):
        load_knowledge(RunPaths(), project_root=fake_knowledge)


def test_malformed_yaml_is_a_hard_failure(fake_knowledge):
    (fake_knowledge / "knowledge/inventories/artists.yaml").write_text(
        "meta: {}\nartists: [\n  - broken", encoding="utf-8"
    )
    with pytest.raises(KnowledgeError):
        load_knowledge(RunPaths(), project_root=fake_knowledge)


def test_registry_is_loaded_when_present(fake_knowledge):
    (fake_knowledge / "knowledge/market/opportunity-registry.yaml").write_text(
        textwrap.dedent(
            """
            schema_version: "1.0.0"
            opportunities:
              - opportunity_id: opp_2026-08-28_abcdef0123
                status: EXPLORE
                created_at: "2026-08-28T00:00:00Z"
                report_ref: null
                state_history:
                  - to: EXPLORE
                    at: "2026-08-28T00:00:00Z"
                    by: system
            """
        ),
        encoding="utf-8",
    )
    kb = load_knowledge(RunPaths(), project_root=fake_knowledge)
    assert len(kb.registry) == 1
    assert kb.registry[0]["opportunity_id"] == "opp_2026-08-28_abcdef0123"
