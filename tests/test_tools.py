import json

import pytest

from shopping_agent import tools
from shopping_agent.tools import checkout, describe_product_image, get_ratings, search_products


def search(**kwargs):
    return json.loads(search_products.invoke(kwargs))


# ---------------------------------------------------------------------------
# search_products
# ---------------------------------------------------------------------------

def test_search_matches_name_description_and_category():
    names = {p["name"] for p in search(query="honey")}
    assert "Clover Honey" in names        # name and category
    assert "Organic Granola" in names     # description only


def test_search_returns_expected_fields():
    [product] = search(query="Manuka")
    assert product == {
        "id": 3,
        "name": "Organic Manuka Honey",
        "category": "honey",
        "price": 29.99,
        "description": "Premium organic Manuka honey from New Zealand",
        "is_organic": True,
    }


def test_search_filters_by_max_price():
    results = search(query="honey", max_price=12.0)
    assert results
    assert all(p["price"] <= 12.0 for p in results)


@pytest.mark.parametrize("is_organic", [True, False])
def test_search_filters_by_organic(is_organic):
    results = search(query="honey", is_organic=is_organic)
    assert results
    assert all(p["is_organic"] is is_organic for p in results)


@pytest.mark.parametrize(("sort_by", "reverse"), [("price_asc", False), ("price_desc", True)])
def test_search_sorts_by_price(sort_by, reverse):
    prices = [p["price"] for p in search(query="honey", sort_by=sort_by)]
    assert prices == sorted(prices, reverse=reverse)


def test_search_default_order_is_by_id():
    ids = [p["id"] for p in search(query="honey")]
    assert ids == sorted(ids)


def test_search_with_no_matches_returns_empty_list():
    assert search(query="motor oil for cars") == []


def test_search_reports_database_errors(monkeypatch, tmp_path):
    monkeypatch.setenv("STORE_DB_PATH", str(tmp_path))  # a directory, not a database
    assert search_products.invoke({"query": "honey"}).startswith("Error:")


# ---------------------------------------------------------------------------
# get_ratings
# ---------------------------------------------------------------------------

def test_get_ratings_returns_one_entry_per_id():
    ratings = json.loads(get_ratings.invoke({"product_ids": [1, 7]}))
    assert [(r["product_id"], r["average_rating"]) for r in ratings] == [(1, 4.62), (7, 4.75)]


# ---------------------------------------------------------------------------
# checkout
# ---------------------------------------------------------------------------

def test_checkout_records_order(query):
    message = checkout.invoke({"product_id": 4})

    assert message.startswith("Order #1 confirmed!")
    assert "'Clover Honey'" in message and "$8.99" in message
    assert query("SELECT product_id, product_name, price FROM orders") == [(4, "Clover Honey", 8.99)]


def test_checkout_unknown_product(query):
    assert checkout.invoke({"product_id": 999}) == "Error: product with ID 999 not found."
    assert query("SELECT COUNT(*) FROM orders")[0][0] == 0


# ---------------------------------------------------------------------------
# describe_product_image
# ---------------------------------------------------------------------------

class FakeVisionLLM:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, []

    def invoke(self, messages):
        self.calls.append(messages)
        if self.error:
            raise self.error
        return type("Response", (), {"content": self.reply})()


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "honey.png"
    path.write_bytes(b"\x89PNG fake image bytes")
    return path


def test_describe_image_sends_image_to_llm(monkeypatch, image):
    reply = json.dumps({"product_type": "honey", "search_query": "honey", "is_organic": True})
    fake = FakeVisionLLM(reply=reply)
    monkeypatch.setattr(tools, "_vision_llm", lambda: fake)

    assert describe_product_image.invoke({"image_path": str(image)}) == reply
    [[message]] = fake.calls
    assert message.content[0]["image_url"]["url"].startswith("data:image/png;base64,")


def test_describe_image_rejects_unsupported_type(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("not an image")
    assert "unsupported image type" in describe_product_image.invoke({"image_path": str(path)})


def test_describe_image_missing_file(tmp_path):
    result = describe_product_image.invoke({"image_path": str(tmp_path / "missing.jpg")})
    assert result.startswith("Error: image not found")


def test_describe_image_reports_llm_failure(monkeypatch, image):
    monkeypatch.setattr(tools, "_vision_llm", lambda: FakeVisionLLM(error=RuntimeError("API down")))
    assert describe_product_image.invoke({"image_path": str(image)}).startswith("Error:")
