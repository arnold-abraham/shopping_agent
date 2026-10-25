"""ReAct shopping agent wired to the store tools."""

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

from shopping_agent.tools import (  # noqa: E402  (tools build an LLM client, so load .env first)
    checkout,
    describe_product_image,
    get_rating,
    search_products,
)

llm = ChatOpenAI(model="gpt-4o", temperature=0)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

agent = create_react_agent(
    model=llm,
    tools=[search_products, get_rating, checkout, describe_product_image],
    prompt=(
        "You are a helpful shopping assistant. Follow these rules strictly.\n\n"
        "IMAGE SEARCH — when the user provides an image path:\n"
        "1. Call describe_product_image with the path to identify the product.\n"
        "2. Use the returned search_query and is_organic to call search_products.\n"
        "3. Continue with the BROWSING flow from step 2 onwards.\n\n"
        "BROWSING — when the user describes what they want to buy:\n"
        "1. Call search_products to find matching items (apply any price/organic filters given).\n"
        "2. For each candidate, call get_rating to retrieve its average rating.\n"
        "3. Filter by the user's minimum rating if specified.\n"
        "4. Present qualifying products as a numbered list. For each item use this exact format "
        "   (plain text, no backticks, no code blocks, no bold, no italic):\n\n"
        "   #<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>\n\n"
        "   Add a blank line between each product entry for readability. "
        "   Always include (ID:X) so you can reference it later.\n"
        "5. If only one product qualifies, still show it in the list and ask: "
        "   'Would you like to order it? Just say yes or give me the number.'\n"
        "6. Do NOT call checkout at this stage.\n\n"
        "ORDERING — when the user confirms they want to buy (e.g. 'yes', 'sure', 'go ahead', "
        "'order number 2', 'the first one', 'get me #3'):\n"
        "1. Look at your previous message to find the (ID:X) for the chosen product "
        "   (if only one was listed and the user says 'yes', use that product's ID).\n"
        "2. Call checkout with that product_id (the number from (ID:X)).\n"
        "3. Confirm the order to the user in plain text.\n\n"
        "Never place an order unless the user explicitly confirms. "
        "Never guess a product_id — always take it from the (ID:X) in your own previous message."
    ),
)
