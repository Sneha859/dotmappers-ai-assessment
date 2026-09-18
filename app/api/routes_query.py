from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse
from app.query.engine import answer_question


router = APIRouter(tags=["Query"])


@router.post(
    "/query",
    response_model=QueryResponse,
)
def query_tickets(request: QueryRequest) -> QueryResponse:
    """
    Answer a natural-language question about support tickets.
    """

    try:
        result = answer_question(request.question)

        return QueryResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc