"""Workflow endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_workflows() -> dict[str, list[dict[str, str]]]:
    """List all workflows."""
    return {"workflows": []}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int) -> dict[str, int | str | None]:
    """Get workflow details."""
    return {
        "id": workflow_id,
        "name": None,
        "status": "pending",
    }
