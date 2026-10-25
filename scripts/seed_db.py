"""Create (or reset) the SQLite store database with seed products and reviews."""

from shopping_agent.config import configure_logging
from shopping_agent.db import init_db

if __name__ == "__main__":
    configure_logging()
    print(f"Database ready at: {init_db()}")
