# Shopping Agent

[![CI](https://github.com/arnold-abraham/shopping_agent/actions/workflows/ci.yml/badge.svg)](https://github.com/arnold-abraham/shopping_agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An AI shopping assistant built with LangChain, GPT-4o, and Streamlit. Chat with it to search a
grocery catalogue, compare ratings, and place orders, or upload a product photo to find
similar items.

## Features

- **Natural-language search:** keyword, max price, and organic filters, plus sorting by price
  ("cheapest first")
- **Ratings:** average review scores fetched for all candidates in one call, with filtering by
  a minimum rating
- **Ordering:** orders are placed only after you explicitly confirm, and saved to SQLite
- **Shop by image:** upload a photo and GPT-4o vision identifies the product and searches for it
- **New chat:** reset the conversation from the sidebar

## Quick start

Requires Python 3.11+ and an OpenAI API key.

```bash
python -m venv .venv && source .venv/bin/activate
make install                 # pip install -e ".[dev]" + pre-commit hooks
cp .env.example .env         # then add your OPENAI_API_KEY
make run                     # http://localhost:8501
```

The SQLite database (`store.db`) is created and seeded automatically on first run. Use
`make seed` to reset products and reviews (existing orders are kept).

### With Docker

```bash
make docker-build
make docker-run              # reads .env, stores the DB in the shopping-agent-data volume
```

## Configuration

All settings are read from environment variables or a `.env` file.

| Variable         | Default    | Description                                          |
| ---------------- | ---------- | ---------------------------------------------------- |
| `OPENAI_API_KEY` | (required) | OpenAI API key                                       |
| `OPENAI_MODEL`   | `gpt-4o`   | Chat model for the agent and image analysis          |
| `STORE_DB_PATH`  | `store.db` | SQLite file path (relative to the working directory) |
| `LOG_LEVEL`      | `INFO`     | Python logging level                                 |

## Example prompts

- `I want organic honey under $20 with 4+ rating`
- `Show me oats, cheapest first`
- `Yes, order number 2`
- Upload an image from `assets/sample_images/` and click **Find similar products**

## How it works

```
Streamlit UI ──► agent (LangChain create_agent + GPT-4o)
                   │
                   ├─ search_products(query, max_price, is_organic, sort_by)
                   ├─ get_ratings(product_ids)
                   ├─ checkout(product_id)
                   └─ describe_product_image(image_path) ──► GPT-4o vision
                   │
                   ▼
                SQLite (products, reviews, orders)
```

The system prompt in [`agent.py`](src/shopping_agent/agent.py) sets out three flows: image
search, browsing, and ordering. The agent never checks out without explicit confirmation,
and only uses product IDs it has already shown to the user. Tools return `Error: ...` strings
instead of raising, so the agent can explain failures in the chat.

## Project layout

```
├── app/streamlit_app.py       # Streamlit chat UI
├── src/shopping_agent/
│   ├── config.py              # settings from environment
│   ├── db.py                  # connection helper, schema, seed data
│   ├── reviews.py             # rating aggregation
│   ├── tools.py               # LangChain tools
│   └── agent.py               # system prompt + build_agent()
├── scripts/seed_db.py         # create/reset the database
├── tests/                     # pytest suite (no API key or network needed)
└── assets/sample_images/      # demo product photos
```

## Development

```bash
make test      # run pytest
make lint      # ruff lint + format check
make format    # auto-fix and format
```

Tests run against a temporary database and a scripted fake chat model, so they need no API
key and make no network calls. CI runs lint and tests on Python 3.11–3.13 for every push to
`main` and every pull request.

## License

[MIT](LICENSE)
