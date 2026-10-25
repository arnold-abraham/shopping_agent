"""Rating queries over the `reviews` table."""

from shopping_agent.db import get_connection


def get_product_rating(product_id: int) -> dict:
    """Return average rating and review count for a single product."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?",
            (product_id,),
        ).fetchone()

    avg = round(row[0], 2) if row and row[0] is not None else 0.0
    count = row[1] if row else 0
    return {"product_id": product_id, "average_rating": avg, "review_count": count}


def get_ratings_for_products(product_ids: list[int]) -> list[dict]:
    """Return ratings for a list of product IDs."""
    if not product_ids:
        return []
    placeholders = ",".join("?" * len(product_ids))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT product_id, AVG(rating), COUNT(*)
            FROM reviews
            WHERE product_id IN ({placeholders})
            GROUP BY product_id
            """,
            product_ids,
        ).fetchall()

    ratings_map = {r[0]: {"average_rating": round(r[1], 2), "review_count": r[2]} for r in rows}
    return [
        {
            "product_id": pid,
            "average_rating": ratings_map.get(pid, {}).get("average_rating", 0.0),
            "review_count":   ratings_map.get(pid, {}).get("review_count", 0),
        }
        for pid in product_ids
    ]
