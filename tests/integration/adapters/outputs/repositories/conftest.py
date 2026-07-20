import pytest
import sqlalchemy


@pytest.fixture
def select_user_by_public_id() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
        SELECT *
        FROM users
        WHERE public_id = :public_id
        """
    )
