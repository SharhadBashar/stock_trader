"""
Base database configuration and setup.
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.sql.elements import TextClause

from settings import DB, DB_HOST, DB_PASSWORD, DB_PORT, DB_USER


load_dotenv()

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB}"

# Database Configuration Parameters:
#
# pool_pre_ping=True:
# - Tests connections before using them, detecting stale or disconnected connections
# - Prevents 'connection has been closed' errors after idle periods
#
# autoflush=False:
# - Prevents automatic flushing of changes to the database before every query
# - Gives explicit control over when changes are persisted
#
# autocommit=False:
# - Forces us to use explicit transactions (this means changes are only commited when you call db.commit())
# - Also allows for rolling back changes if errors occur during processing

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_db() -> Generator[Session, Any, Any]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, Any, Any]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def execute_query(
    sql: TextClause,
    params: dict | None = None,
    fetch_method: str = "fetchall",
) -> list[dict] | list | Any:
    """Execute a SQL query and return results based on fetch_method.

    Args:
        sql: SQL query to execute
        params: Query parameters for bind variables
        fetch_method: How to fetch results - "mappings" or "fetchall"

    Returns:
        List of dicts if fetch_method="mappings", list of tuples if "fetchall",
        or raw Result object otherwise
    """
    with get_db_session() as db:
        result = db.execute(sql, params)
        if fetch_method == "mappings":
            return [dict(row) for row in result.mappings().all()]
        elif fetch_method == "fetchall":
            return result.fetchall()
        return result
