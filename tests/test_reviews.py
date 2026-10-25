from shopping_agent.reviews import get_ratings_for_products


def test_returns_average_and_count():
    [rating] = get_ratings_for_products([1])
    assert rating == {"product_id": 1, "average_rating": 4.62, "review_count": 4}


def test_preserves_requested_order():
    ids = [7, 1, 3]
    assert [r["product_id"] for r in get_ratings_for_products(ids)] == ids


def test_unknown_product_has_zero_rating():
    [rating] = get_ratings_for_products([999])
    assert rating == {"product_id": 999, "average_rating": 0.0, "review_count": 0}


def test_empty_input_returns_empty_list():
    assert get_ratings_for_products([]) == []
