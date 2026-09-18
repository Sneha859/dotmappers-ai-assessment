from fastapi import APIRouter, HTTPException

from app.anomaly.detector import detect_anomalies
from app.models.schemas import AnomalyResponse


router = APIRouter(tags=["Anomalies"])


@router.get(
    "/anomalies",
    response_model=AnomalyResponse,
)
def get_anomalies() -> AnomalyResponse:
    """
    Run the configured anomaly-detection rules.
    """

    try:
        result = detect_anomalies()

        return AnomalyResponse(**result)

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Anomaly detection failed: {exc}",
        ) from exc