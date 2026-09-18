from fastapi import FastAPI

from app.api.routes_anomaly import router as anomaly_router
from app.api.routes_health import router as health_router
from app.api.routes_query import router as query_router


app = FastAPI(
    title="DotMappers AI Support Ticket Intelligence",
    description=(
        "AI-powered support ticket analytics using "
        "Ollama, DuckDB, and deterministic anomaly detection."
    ),
    version="1.0.0",
)


app.include_router(health_router)
app.include_router(query_router)
app.include_router(anomaly_router)