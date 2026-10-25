PY_DIRS := src tests app scripts
IMAGE   := shopping-agent

.PHONY: help install seed run test lint format docker-build docker-run

help:  ## Show available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-14s %s\n", $$1, $$2}'

install:  ## Install the package with dev tools and git hooks
	pip install -e ".[dev]"
	pre-commit install

seed:  ## Create or reset the store database
	python scripts/seed_db.py

run:  ## Start the Streamlit app
	streamlit run app/streamlit_app.py

test:  ## Run the test suite
	pytest

lint:  ## Check linting and formatting
	ruff check $(PY_DIRS)
	ruff format --check $(PY_DIRS)

format:  ## Auto-fix lint issues and format code
	ruff check --fix $(PY_DIRS)
	ruff format $(PY_DIRS)

docker-build:  ## Build the Docker image
	docker build -t $(IMAGE) .

docker-run:  ## Run the app in Docker on http://localhost:8501
	docker run --rm --env-file .env -p 8501:8501 -v shopping-agent-data:/app/data $(IMAGE)
