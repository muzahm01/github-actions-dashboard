"""Job endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{job_id}")
async def get_job(job_id: int) -> dict[str, int | str | None]:
    """Get job details."""
    return {
        "id": job_id,
        "name": None,
        "status": None,
    }


@router.get("/{job_id}/logs")
async def get_job_logs(job_id: int) -> dict[str, int | str | None]:
    """Get job logs."""
    return {
        "job_id": job_id,
        "log_content": None,
    }
