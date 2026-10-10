"""
backend/config.py
=================
Centralized configuration for the Crop Disease Detection backend.

All values are read from environment variables (set in backend/.env locally,
or injected by the hosting environment in production).

DO NOT hard-code secrets here.  Add new settings as os.getenv() calls.
"""

import os

from dotenv import load_dotenv

# Load .env from the same directory as this file (backend/.env)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


# ---------------------------------------------------------------------------
# Database — PostgreSQL
# ---------------------------------------------------------------------------
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DB_NAME: str = os.getenv("DB_NAME", "crop_disease_db")
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

# Async URL used by SQLAlchemy + asyncpg (FastAPI, seed scripts, repositories)
DATABASE_URL: str = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Sync URL used by Alembic CLI (psycopg2 driver)
DATABASE_URL_SYNC: str = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# ---------------------------------------------------------------------------
# ML Confidence & Rejection
# ---------------------------------------------------------------------------
# Softmax probability threshold required to accept a prediction as confident.
# Default 0.70 (70%).  Predictions below this are flagged 'low_confidence'.
#
# NOTE: Softmax probability is NOT calibrated real-world probability.
# It represents the neural network's relative class distribution.
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))

# Maximum allowed upload image size in bytes (default: 10 MB)
MAX_UPLOAD_SIZE_BYTES: int = int(
    os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))
)
# Directory for storing scan image uploads
UPLOAD_DIR: str = os.getenv(
    "UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads")
)


# ---------------------------------------------------------------------------
# Clerk Authentication
# ---------------------------------------------------------------------------
CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
CLERK_JWKS_URL: str = os.getenv(
    "CLERK_JWKS_URL",
    "https://teaching-terrier-8084.clerk.accounts.dev/.well-known/jwks.json",
)
CLERK_ISSUER: str = os.getenv(
    "CLERK_ISSUER",
    "https://teaching-terrier-8084.clerk.accounts.dev",
)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
APP_ENV: str = os.getenv("APP_ENV", "development")    # development | production
DEBUG_SQL: bool = os.getenv("DEBUG_SQL", "false").lower() == "true"


# ---------------------------------------------------------------------------
# Weather Provider (Module 13 - Open-Meteo default)
# ---------------------------------------------------------------------------
WEATHER_PROVIDER: str = os.getenv("WEATHER_PROVIDER", "open-meteo")
WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
WEATHER_CACHE_MINUTES: int = int(os.getenv("WEATHER_CACHE_MINUTES", "30"))


# ---------------------------------------------------------------------------
# LLM Advisory Provider (Module 14 - Groq API with Multi-Key Rotation)
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_API_KEY_1: str = os.getenv("GROQ_API_KEY_1", "")
GROQ_API_KEY_2: str = os.getenv("GROQ_API_KEY_2", "")
GROQ_API_KEY_3: str = os.getenv("GROQ_API_KEY_3", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_API_URL: str = os.getenv(
    "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
)
GROQ_TIMEOUT_SECONDS: float = float(os.getenv("GROQ_TIMEOUT_SECONDS", "45.0"))

