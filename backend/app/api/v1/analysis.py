"""Error analysis endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request body for error analysis."""

    log_id: int


class SimilarErrorRequest(BaseModel):
    """Request body for similar error search."""

    log_id: int
    limit: int = 5


@router.post("/analyze")
async def analyze_error(request: AnalysisRequest) -> dict[str, int | str | None]:
    """Analyze error with LLM."""
    return {
        "log_id": request.log_id,
        "root_cause": None,
        "status": "pending",
    }


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: int) -> dict[str, int | str | None]:
    """Get existing analysis."""
    return {
        "id": analysis_id,
        "root_cause": None,
        "status": None,
    }


@router.post("/similar")
async def find_similar_errors(
    request: SimilarErrorRequest,
) -> dict[str, int | list[dict[str, str]]]:
    """Find similar errors."""
    return {
        "log_id": request.log_id,
        "similar_errors": [],
    }
