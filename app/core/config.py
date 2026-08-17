import os

from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000"
)


if not GITHUB_CLIENT_ID:
    raise ValueError("GITHUB_CLIENT_ID is not set")

if not GITHUB_CLIENT_SECRET:
    raise ValueError("GITHUB_CLIENT_SECRET is not set")