from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language question about support tickets.",
    )


class GeneratedQuery(BaseModel):
    intent: str
    sql: str
    explanation: str


class QueryResponse(BaseModel):
    question: str
    sql: str
    explanation: str
    answer: str
    results: list[dict[str, Any]]


class IQRAnomalyResult(BaseModel):
    rule: str
    reference_time: str
    week_only: bool
    q1_hours: float | None
    q3_hours: float | None
    iqr_hours: float | None
    upper_bound_hours: float | None
    anomaly_count: int
    anomalies: list[dict[str, Any]]


class StalePriorityAnomalyResult(BaseModel):
    rule: str
    reference_time: str
    age_threshold_hours: float
    anomaly_count: int
    anomalies: list[dict[str, Any]]


class AnomalyResponse(BaseModel):
    reference_time: str
    resolution_time_anomalies: IQRAnomalyResult
    weekly_resolution_time_anomalies: IQRAnomalyResult
    stale_priority_tickets: StalePriorityAnomalyResult
    total_anomalies: int


class HealthResponse(BaseModel):
    status: str
    dataset_rows: int
    llm_model: str