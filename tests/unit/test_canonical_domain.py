from domain.canonical import ClaimStatus


def test_claim_status_active_default() -> None:
    assert ClaimStatus.ACTIVE.value == "active"


def test_claim_lifecycle_values() -> None:
    values = {status.value for status in ClaimStatus}
    assert "superseded" in values
    assert "retracted" in values
