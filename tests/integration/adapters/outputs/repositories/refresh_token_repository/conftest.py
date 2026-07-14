import pytest
import sqlalchemy


@pytest.fixture
def select_revoked_at_column_by_jti() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT revoked_at
        FROM refresh_tokens
        WHERE jti = :jti;
        """
    )


@pytest.fixture
def select_refresh_token_by_jti() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT *
        FROM refresh_tokens
        WHERE jti = :jti;
        """
    )


@pytest.fixture
def select_all_refresh_token_order_by_jti() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT *
        FROM refresh_tokens
        ORDER BY jti;
        """
    )


@pytest.fixture
def select_jti_column_by_jti() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT jti
        FROM refresh_tokens
        WHERE jti = :jti
        """
    )
