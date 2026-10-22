import os

import psycopg
from fastapi import FastAPI

from app.api.simulator import router as simulator_router
from app.api.incidents import router as incident_router

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/oncall",
)

app = FastAPI(title="Hero Vired Assignment API", version="0.1.0")
app.include_router(simulator_router)
app.include_router(incident_router)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/api/v1/readiness")
def readiness() -> dict[str, str]:
    with psycopg.connect(DATABASE_URL, connect_timeout=2) as connection:
        connection.execute("SELECT 1")
    return {"status": "ready", "database": "ok"}
