from ontology.loader import load_ontology_snapshot


def test_load_ontology_snapshot_reads_core_yaml() -> None:
    snapshot = load_ontology_snapshot()
    assert snapshot.version == "0.1.0"
    assert "entity" in snapshot.entity_type_ids
    assert "relates_to" in snapshot.relationship_type_ids
    assert "core.yaml" in snapshot.source_files
