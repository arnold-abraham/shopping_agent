"""LangChain tools the shopping agent can call.

Tools never raise: failures are returned as "Error: ..." strings so the agent can
explain the problem to the user instead of crashing the conversation.
"""

import base64
import json
import logging
import sqlite3
from pathlib import Path
from typing import Literal, Optional

from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from shopping_agent.config import get_settings, require_api_key
from shopping_agent.db import get_connection
from shopping_agent.reviews import get_ratings_for_products

logger = logging.getLogger(__name__)

IMAGE_MIME_TYPES = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
}


def _vision_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model, temperature=0, api_key=require_api_key(settings)
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def search_products(
    query: str,
    max_price: Optional[float] = None,
    is_organic: Optional[bool] = None,
    sort_by: Optional[Literal["price_asc", "price_desc"]] = None,
) -> str:
    """
    Search the product database by keyword (matched against name, description, and category).
    Optionally filter by maximum price and/or organic status, and sort by price
    ("price_asc" for cheapest first, "price_desc" for most expensive first).
    Returns a JSON array of matching products, each with: id, name, category, price,
    description, is_organic.
    """
    sql = "SELECT id, name, category, price, description, is_organic FROM products WHERE 1=1"
    params: list = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    if is_organic is not None:
        sql += " AND is_organic = ?"
        params.append(1 if is_organic else 0)

    sql += {
        "price_asc":  " ORDER BY price ASC, id",
        "price_desc": " ORDER BY price DESC, id",
    }.get(sort_by, " ORDER BY id")

    try:
        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error:
        logger.exception("search_products failed")
        return "Error: the product catalogue is unavailable right now."

    products = [
        {
            "id":          row["id"],
            "name":        row["name"],
            "category":    row["category"],
            "price":       row["price"],
            "description": row["description"],
            "is_organic":  bool(row["is_organic"]),
        }
        for row in rows
    ]
    return json.dumps(products)


@tool
def get_ratings(product_ids: list[int]) -> str:
    """
    Get the average customer rating and total review count for several products at once.
    Pass the IDs of all candidate products in a single call.
    Returns a JSON array of objects with: product_id, average_rating, review_count.
    """
    try:
        result = get_ratings_for_products(product_ids)
    except sqlite3.Error:
        logger.exception("get_ratings failed")
        return "Error: ratings are unavailable right now."
    return json.dumps(result)


@tool
def checkout(product_id: int) -> str:
    """
    Place an order for the given product ID. Saves the order to the database and returns
    a confirmation message with the order ID, product name, and price.
    """
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT name, price FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            if not row:
                return f"Error: product with ID {product_id} not found."

            name, price = row["name"], row["price"]
            cursor = conn.execute(
                "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
                (product_id, name, price),
            )
            order_id = cursor.lastrowid
    except sqlite3.Error:
        logger.exception("checkout failed for product %s", product_id)
        return "Error: the order could not be placed. Please try again."

    logger.info("Order #%s placed for product %s", order_id, product_id)
    return (
        f"Order #{order_id} confirmed! '{name}' has been successfully ordered for ${price:.2f}. "
        f"Your order will arrive in 3-5 business days. Thank you for shopping with us!"
    )


@tool
def describe_product_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.
    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """
    path = Path(image_path)
    mime = IMAGE_MIME_TYPES.get(path.suffix.lower())
    if mime is None:
        return f"Error: unsupported image type '{path.suffix}'. Use JPG, PNG, or WEBP."
    if not path.is_file():
        return f"Error: image not found at {image_path}."

    image_data = base64.b64encode(path.read_bytes()).decode()

    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{image_data}"},
        },
        {
            "type": "text",
            "text": (
                "Look at this product image and extract its key attributes. "
                "Return ONLY a JSON object with these fields:\n"
                "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                "- search_query: a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                "- is_organic: true if the label says organic, false if not, null if unclear\n"
                "- description: one sentence describing the product"
            ),
        },
    ])

    try:
        response = _vision_llm().invoke([message])
    except Exception:
        logger.exception("Image analysis failed for %s", image_path)
        return "Error: the image could not be analysed right now."
    return response.content
