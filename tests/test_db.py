import sqlite3

import pytest

from shopping_agent.db import PRODUCTS, REVIEWS, ensure_db, get_connection, init_db


def test_init_db_creates_tables(query):
    tables = {row[0] for row in query("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"products", "reviews", "orders"} <= tables


def test_init_db_seeds_products_and_reviews(query):
    assert query("SELECT COUNT(*) FROM products")[0][0] == len(PRODUCTS)
    assert query("SELECT COUNT(*) FROM reviews")[0][0] == len(REVIEWS)


def test_init_db_is_idempotent_and_keeps_orders(db_path, query):
    with get_connection() as conn:
        conn.execute("INSERT INTO orders (product_id, product_name, price) VALUES (1, 'x', 1.0)")

    init_db(db_path)

    assert query("SELECT COUNT(*) FROM reviews")[0][0] == len(REVIEWS)
    assert query("SELECT COUNT(*) FROM orders")[0][0] == 1


def test_ensure_db_creates_missing_database(tmp_path):
    path = tmp_path / "nested" / "new.db"

    ensure_db(path)

    assert path.exists()
    with get_connection(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == len(PRODUCTS)


def test_ensure_db_leaves_existing_database_alone(db_path, query):
    with get_connection() as conn:
        conn.execute("DELETE FROM reviews")

    ensure_db(db_path)

    assert query("SELECT COUNT(*) FROM reviews")[0][0] == 0


def test_get_connection_rolls_back_on_error(query):
    with pytest.raises(RuntimeError), get_connection() as conn:
        conn.execute("DELETE FROM reviews")
        raise RuntimeError("boom")

    assert query("SELECT COUNT(*) FROM reviews")[0][0] == len(REVIEWS)


def test_foreign_keys_are_enforced():
    with pytest.raises(sqlite3.IntegrityError), get_connection() as conn:
        conn.execute("INSERT INTO orders (product_id, product_name, price) VALUES (999, 'x', 1.0)")
