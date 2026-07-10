from domain.errors import DomainError
from domain.identity import OwnerContext


class LocalPolicyService:
    """MVP single-user policy (ADR-009)."""

    def authorize_owner(self, ctx: OwnerContext, owner_id: object) -> None:
        if ctx.owner_id != owner_id:
            raise DomainError("Unauthorized access")
