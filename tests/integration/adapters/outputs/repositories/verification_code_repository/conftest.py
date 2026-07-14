import uuid
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy

from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.value_objects.code import Code


@pytest.fixture
def verification_code():
    return VerificationCode(
        code=Code('123456'),
        user_public_id=uuid.uuid4(),
        type=CodeType.CHANGE_PASSWORD,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        used_at=None,
        payload=None,
    )


@pytest.fixture
def select_verification_code_by_code() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT *
        FROM verification_codes
        WHERE code = :code
        """
    )


@pytest.fixture
def select_code_column_by_code() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT code
        FROM verification_codes
        WHERE code = :code
        """
    )


@pytest.fixture
def select_used_at_column_by_code() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT used_at
        FROM verification_codes
        WHERE code = :code
        """
    )


@pytest.fixture
def select_code_column_by_user_public_id() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT code
        FROM verification_codes
        WHERE user_public_id = :user_public_id
        """
    )
