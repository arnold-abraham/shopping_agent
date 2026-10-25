import sqlite3

import pytest

from shopping_agent.db import init_db


@pytest.fixture(autouse=True)
def db_path(tmp_path, monkeypatch):
    """Point every test at a fresh, seeded database and a dummy API key."""
    path = tmp_path / "store.db"
    monkeypatch.setenv("STORE_DB_PATH", str(path))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    init_db(path)
    return path


@pytest.fixture
def query(db_path):
    """Run a read-only query against the test database."""

    def _query(sql, params=()):
        with sqlite3.connect(db_path) as conn:
            return conn.execute(sql, params).fetchall()

    return _query
