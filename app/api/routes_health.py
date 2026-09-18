from fastapi import APIRouter

from app.data.loader import load_dataframe
from app.llm.client import MODEL_NAME
from app.models.schemas import HealthResponse


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """
    Return application health and basic dependency information.
    """

    df = load_dataframe()

    return HealthResponse(
        status="healthy",
        dataset_rows=len(df),
        llm_model=MODEL_NAME,
    )