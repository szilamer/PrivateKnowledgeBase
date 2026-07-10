from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class ApprovalAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT_AND_APPROVE = "edit_and_approve"
    MERGE = "merge"
    DEFER = "defer"


class ApprovalDecision(BaseModel):
    id: UUID
    proposal_id: UUID
    actor_id: UUID
    action: ApprovalAction
    rationale: str | None = None
    edited_payload: dict[str, object] | None = None
    correlation_id: str
    created_at: datetime
