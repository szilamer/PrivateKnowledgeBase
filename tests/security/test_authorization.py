from uuid import uuid4

import pytest
from application.policy import LocalPolicyService
from domain.errors import DomainError
from domain.identity import DEFAULT_OWNER_ID, OwnerContext


def test_authorize_owner_allows_default_owner() -> None:
    policy = LocalPolicyService()
    owner = OwnerContext(owner_id=DEFAULT_OWNER_ID)
    policy.authorize_owner(owner, DEFAULT_OWNER_ID)


def test_authorize_owner_blocks_foreign_owner() -> None:
    policy = LocalPolicyService()
    owner = OwnerContext(owner_id=DEFAULT_OWNER_ID)
    foreign_id = uuid4()
    with pytest.raises(DomainError, match="Unauthorized"):
        policy.authorize_owner(owner, foreign_id)


def test_owner_context_mismatch_blocks_access() -> None:
    policy = LocalPolicyService()
    owner = OwnerContext(owner_id=uuid4())
    with pytest.raises(DomainError):
        policy.authorize_owner(owner, DEFAULT_OWNER_ID)
