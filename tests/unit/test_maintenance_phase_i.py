from domain.operations import OperationsStatus, PipelineHealthSnapshot


def test_operations_status_summary_hu() -> None:
    status = OperationsStatus(
        pending_outbox_events=2,
        pipeline=PipelineHealthSnapshot(
            extraction_pending=5,
            knowledge_pending=3,
            extraction_failed=1,
        ),
        maintenance_recommended=True,
        status_summary_hu="teszt",
    )
    assert status.pipeline.extraction_pending == 5
    assert status.maintenance_recommended is True


def test_pipeline_health_defaults() -> None:
    pipeline = PipelineHealthSnapshot()
    assert pipeline.triage_pending == 0
    assert pipeline.embedding_model_mismatch_versions == 0
