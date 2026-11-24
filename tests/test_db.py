from sqlalchemy import text

from forest_ai.db.session import engine



def test_database_is_reachable():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()

    assert result == 1