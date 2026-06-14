# Shopping Agent

An AI-powered shopping assistant built with LangGraph and GPT-4o. Search products, check ratings, and place orders through a chat interface.

## Features

- Natural language product search (keyword, price, organic filters)
- Automatic rating lookup per product
- Order confirmation via chat
- Image-based product search — upload a photo to find similar items

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then add your OpenAI API key
python setup_db.py     # seed the SQLite database
```

## Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Example prompts

- `"I want organic honey under $20 with 4+ rating"`
- `"Show me oats, cheapest first"`
- Upload an image from `resources/` and click **Find similar products**
