from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.database import engine


app = FastAPI(
    title="CodeLens API",
    description="AI-Powered Codebase Intelligence Copilot",
    version="0.1.0"
)

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