from uuid import UUID

from pydantic import BaseModel

# Local single-user MVP seed owner (ADR-009).
DEFAULT_OWNER_ID = UUID("00000000-0000-4000-8000-000000000001")


class OwnerContext(BaseModel):
    owner_id: UUID = DEFAULT_OWNER_ID
