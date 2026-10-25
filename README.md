# Shopping Agent

An AI-powered shopping assistant built with LangGraph and GPT-4o. Search products, check ratings, and place orders through a chat interface.

## Features

- Natural language product search (keyword, price, organic filters)
- Automatic rating lookup per product
- Order confirmation via chat
- Image-based product search — upload a photo to find similar items

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env        # then add your OpenAI API key
python scripts/seed_db.py   # seed the SQLite database
```

## Run

```bash
streamlit run app/streamlit_app.py
```

Open http://localhost:8501 in your browser.

## Example prompts

- `"I want organic honey under $20 with 4+ rating"`
- `"Show me oats, cheapest first"`
- Upload an image from `assets/sample_images/` and click **Find similar products**
