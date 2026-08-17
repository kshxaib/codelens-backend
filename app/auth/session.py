import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()


SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

if not SESSION_SECRET_KEY:
    raise ValueError("SESSION_SECRET_KEY is not set")


def configure_session(app):
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET_KEY,
        session_cookie="codelens_session",
        max_age=60 * 60 * 24 * 7,
        same_site="lax",
        https_only=False,
    )