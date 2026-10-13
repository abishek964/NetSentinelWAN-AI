"""
db.py — connection helper for the AI engine.

Unlike the FastAPI backend (which uses a connection pool to serve many
concurrent requests), this module opens ONE connection at a time, since
ai_engine scripts (train.py, predict.py) run as standalone batch jobs,
not as a server handling concurrent traffic.
"""

import os
import psycopg
from dotenv import load_dotenv

# Load variables from .env into the environment (DATABASE_URL, etc.)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not found. Make sure ai_engine/.env exists and contains it."
    )


def get_connection():
    """
    Opens and returns a new psycopg connection to the Neon database.
    Caller is responsible for closing it (or using it in a `with` block).
    """
    return psycopg.connect(DATABASE_URL)