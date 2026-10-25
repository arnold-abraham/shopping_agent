import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from shopping_agent.agent import TOOLS, build_agent
from shopping_agent.config import ConfigError


class FakeToolCallingModel(GenericFakeChatModel):
    """Replays scripted AI messages; tool binding is a no-op."""

    def bind_tools(self, tools, **kwargs):
        return self


def tool_call(name, args, call_id):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def run(script, user_message):
    agent = build_agent(model=FakeToolCallingModel(messages=iter(script)))
    return agent.invoke({"messages": [{"role": "user", "content": user_message}]})["messages"]


def tool_results(messages):
    return {m.name: m.content for m in messages if isinstance(m, ToolMessage)}


def test_agent_registers_all_tools():
    assert {t.name for t in TOOLS} == {
        "search_products",
        "get_ratings",
        "checkout",
        "describe_product_image",
    }


def test_browsing_flow_searches_then_rates():
    messages = run(
        [
            tool_call(
                "search_products", {"query": "honey", "is_organic": True, "max_price": 15}, "1"
            ),
            tool_call("get_ratings", {"product_ids": [1]}, "2"),
            AIMessage(content="#1. Organic Raw Honey (ID:1) — $14.99 ★4.62 — organic"),
        ],
        "organic honey under $15",
    )

    results = tool_results(messages)
    assert '"name": "Organic Raw Honey"' in results["search_products"]
    assert '"average_rating": 4.62' in results["get_ratings"]
    assert messages[-1].content.startswith("#1. Organic Raw Honey (ID:1)")


def test_ordering_flow_places_order(query):
    messages = run(
        [tool_call("checkout", {"product_id": 1}, "1"), AIMessage(content="Your order is placed.")],
        "yes, order it",
    )

    assert tool_results(messages)["checkout"].startswith("Order #1 confirmed!")
    assert query("SELECT product_id FROM orders") == [(1,)]


def test_build_agent_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    with pytest.raises(ConfigError):
        build_agent()
