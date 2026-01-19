"""Celery tasks for error analysis with LLM."""
import asyncio
import logging

from app.config import get_settings
from app.infrastructure.external.embedding_client import EmbeddingClient
from app.infrastructure.external.llm_client import ClaudeClient
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def run_async(coro):  # type: ignore[no-untyped-def]
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=2)
def analyze_error_log(  # type: ignore[no-untyped-def]
    self,
    log_id: int,
    log_content: str,
    framework: str = "unknown",
    job_name: str = "unknown",
) -> dict:
    """Analyze an error log using Claude LLM."""
    logger.info(f"Analyzing error log {log_id}")

    async def _analyze() -> dict:
        client = ClaudeClient(settings)
        result = await client.analyze_error(
            log_content=log_content,
            framework=framework,
            job_name=job_name,
        )
        return {
            "log_id": log_id,
            "root_cause": result.root_cause,
            "error_summary": result.error_summary,
            "suggested_fixes": result.suggested_fixes,
            "prevention_tips": result.prevention_tips,
            "confidence_score": result.confidence_score,
            "related_documentation": result.related_documentation,
            "tokens_used": result.tokens_used,
        }

    try:
        return run_async(_analyze())
    except Exception as e:
        logger.error(f"Failed to analyze log {log_id}: {e}")
        raise self.retry(exc=e, countdown=120) from e


@celery_app.task(bind=True, max_retries=2)
def generate_embedding(self, log_id: int, content: str) -> dict:  # type: ignore[no-untyped-def]
    """Generate embedding for log content."""
    logger.info(f"Generating embedding for log {log_id}")

    async def _embed() -> dict:
        client = EmbeddingClient(settings)
        embedding = await client.create_embedding(content)
        return {
            "log_id": log_id,
            "embedding_size": len(embedding),
        }

    try:
        return run_async(_embed())
    except Exception as e:
        logger.error(f"Failed to generate embedding for log {log_id}: {e}")
        raise self.retry(exc=e, countdown=60) from e


@celery_app.task
def batch_generate_embeddings(log_ids: list[int], contents: list[str]) -> dict:
    """Generate embeddings for multiple logs in batch."""
    logger.info(f"Generating embeddings for {len(log_ids)} logs")

    async def _batch_embed() -> dict:
        client = EmbeddingClient(settings)
        embeddings = await client.create_embeddings_batch(contents)
        return {
            "logs_processed": len(log_ids),
            "embeddings_generated": len(embeddings),
        }

    try:
        return run_async(_batch_embed())
    except Exception as e:
        logger.error(f"Failed to batch generate embeddings: {e}")
        return {"error": str(e), "logs_processed": 0}


@celery_app.task
def summarize_run_failures(run_id: int, failures: list[dict]) -> dict:
    """Summarize all failures in a workflow run."""
    logger.info(f"Summarizing failures for run {run_id}")

    async def _summarize() -> dict:
        client = ClaudeClient(settings)
        summary = await client.summarize_failures(failures)
        return {
            "run_id": run_id,
            "failure_count": len(failures),
            "summary": summary,
        }

    try:
        return run_async(_summarize())
    except Exception as e:
        logger.error(f"Failed to summarize run {run_id}: {e}")
        return {"error": str(e), "run_id": run_id}
