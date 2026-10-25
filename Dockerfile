FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STORE_DB_PATH=/app/data/store.db

WORKDIR /app

RUN useradd --create-home appuser

# Install dependencies first so they are cached between code changes.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install .

COPY app ./app
RUN mkdir -p /app/data && chown appuser /app/data

USER appuser
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
