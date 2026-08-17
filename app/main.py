from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.database import engine
from app.auth.session import configure_session
from app.auth.routes import router as auth_router
from app.repositories.routes import router as repository_router

app = FastAPI(
    title="CodeLens API",
    description="AI-Powered Codebase Intelligence Copilot",
    version="0.1.0"
)

configure_session(app)


# Frontend development server
origins = [
    "http://localhost:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(repository_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "codelens-backend"
    }


@app.get("/api/health/db")
def database_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "status": "ok",
        "database": "postgresql",
        "result": value
    }