"""Workflow run endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_runs() -> dict[str, list[dict[str, str]]]:
    """List all workflow runs."""
    return {"runs": []}


@router.get("/{run_id}")
async def get_run(run_id: int) -> dict[str, int | str | None]:
    """Get workflow run details."""
    return {
        "id": run_id,
        "status": None,
        "conclusion": None,
    }
