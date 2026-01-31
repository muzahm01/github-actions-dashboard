"""Celery tasks for error analysis with LLM."""

import asyncio
import logging
from datetime import datetime

from app.config import get_settings
from app.infrastructure.database.models.error_analysis import ErrorAnalysis
from app.infrastructure.database.repositories.error_analysis_repo import (
    ErrorAnalysisRepository,
)
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.external.embedding_client import EmbeddingClient
from app.infrastructure.external.llm_client import ClaudeClient
from app.infrastructure.websocket.pubsub import (
    publish_analysis_complete,
    publish_embedding_generated,
)
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
    log_content: str | None = None,
    framework: str = "unknown",
    job_name: str = "unknown",
    save_to_db: bool = True,
) -> dict:
    """
    Analyze an error log using Claude LLM and optionally save to database.

    If log_content is not provided, it will be fetched from the database.
    """
    logger.info(f"Analyzing error log {log_id}")

    async def _analyze() -> dict:
        session_factory = get_session_factory()
        async with session_factory() as session:
            log_repo = LogRepository(session)
            analysis_repo = ErrorAnalysisRepository(session)

            # Fetch log content if not provided
            content = log_content
            if content is None:
                log = await log_repo.get_by_id(log_id)
                if log is None:
                    return {
                        "log_id": log_id,
                        "error": "Log not found",
                        "success": False,
                    }
                content = log.error_content or log.log_content
                if not content:
                    return {
                        "log_id": log_id,
                        "error": "Log has no content",
                        "success": False,
                    }

            # Call LLM for analysis
            client = ClaudeClient(settings)
            result = await client.analyze_error(
                log_content=content,
                framework=framework,
                job_name=job_name,
            )

            result_dict = {
                "log_id": log_id,
                "root_cause": result.root_cause,
                "error_summary": result.error_summary,
                "suggested_fixes": result.suggested_fixes,
                "prevention_tips": result.prevention_tips,
                "confidence_score": result.confidence_score,
                "related_documentation": result.related_documentation,
                "tokens_used": result.tokens_used,
                "success": True,
            }

            # Save to database if requested
            if save_to_db:
                # Check if analysis already exists
                existing = await analysis_repo.get_by_log_id(log_id)
                if existing:
                    # Update existing analysis
                    existing.root_cause = result.root_cause
                    existing.error_summary = result.error_summary
                    existing.suggested_fixes = result.suggested_fixes
                    existing.prevention_tips = result.prevention_tips
                    existing.confidence_score = result.confidence_score
                    existing.related_documentation = result.related_documentation
                    existing.llm_model = settings.claude_model
                    existing.llm_tokens_used = result.tokens_used
                    existing.analyzed_at = datetime.utcnow()
                    await analysis_repo.update(existing)
                    result_dict["analysis_id"] = existing.id
                else:
                    # Create new analysis
                    analysis = ErrorAnalysis(
                        log_id=log_id,
                        root_cause=result.root_cause,
                        error_summary=result.error_summary,
                        suggested_fixes=result.suggested_fixes,
                        prevention_tips=result.prevention_tips,
                        confidence_score=result.confidence_score,
                        related_documentation=result.related_documentation,
                        llm_model=settings.claude_model,
                        llm_tokens_used=result.tokens_used,
                        analyzed_at=datetime.utcnow(),
                    )
                    created = await analysis_repo.create(analysis)
                    result_dict["analysis_id"] = created.id

                await session.commit()

                # Publish WebSocket event for analysis completion
                if "analysis_id" in result_dict:
                    publish_analysis_complete(
                        log_id=log_id,
                        analysis_id=result_dict["analysis_id"],
                        data={
                            "error_summary": result.error_summary,
                            "confidence_score": result.confidence_score,
                        },
                    )

            return result_dict

    try:
        return run_async(_analyze())
    except Exception as e:
        logger.error(f"Failed to analyze log {log_id}: {e}")
        raise self.retry(exc=e, countdown=120) from e


@celery_app.task(bind=True, max_retries=2)
def generate_embedding(  # type: ignore[no-untyped-def]
    self,
    log_id: int,
    content: str | None = None,
) -> dict:
    """
    Generate embedding for log content and save to database.

    If content is not provided, it will be fetched from the database.
    The generated embedding is saved back to the log record.
    """
    logger.info(f"Generating embedding for log {log_id}")

    async def _embed() -> dict:
        session_factory = get_session_factory()
        async with session_factory() as session:
            log_repo = LogRepository(session)

            # Fetch log if content not provided
            log_content = content
            if log_content is None:
                log = await log_repo.get_by_id(log_id)
                if log is None:
                    return {
                        "log_id": log_id,
                        "error": "Log not found",
                        "success": False,
                    }
                # Use error_content if available, otherwise full log
                log_content = log.error_content or log.log_content
                if not log_content:
                    return {
                        "log_id": log_id,
                        "error": "Log has no content",
                        "success": False,
                    }

            # Generate embedding
            client = EmbeddingClient(settings)
            try:
                embedding = await client.create_embedding(log_content)
            finally:
                await client.close()

            # Save embedding to database
            updated_log = await log_repo.update_embedding(log_id, embedding)
            await session.commit()

            if updated_log is None:
                return {
                    "log_id": log_id,
                    "error": "Failed to update log with embedding",
                    "success": False,
                }

            # Publish WebSocket event for embedding generation
            publish_embedding_generated(
                log_id=log_id,
                embedding_size=len(embedding),
            )

            return {
                "log_id": log_id,
                "embedding_size": len(embedding),
                "success": True,
            }

    try:
        return run_async(_embed())
    except Exception as e:
        logger.error(f"Failed to generate embedding for log {log_id}: {e}")
        raise self.retry(exc=e, countdown=60) from e


@celery_app.task
def batch_generate_embeddings(log_ids: list[int], contents: list[str] | None = None) -> dict:
    """
    Generate embeddings for multiple logs in batch and save to database.

    If contents is not provided, they will be fetched from the database.
    """
    logger.info(f"Generating embeddings for {len(log_ids)} logs")

    async def _batch_embed() -> dict:
        session_factory = get_session_factory()
        async with session_factory() as session:
            log_repo = LogRepository(session)

            # Fetch contents from DB if not provided
            log_contents = contents
            if log_contents is None:
                log_contents = []
                for log_id in log_ids:
                    log = await log_repo.get_by_id(log_id)
                    if log:
                        content = log.error_content or log.log_content or ""
                        log_contents.append(content)
                    else:
                        log_contents.append("")

            # Filter out empty contents
            valid_pairs = [
                (log_id, content)
                for log_id, content in zip(log_ids, log_contents, strict=False)
                if content
            ]

            if not valid_pairs:
                return {
                    "logs_processed": 0,
                    "embeddings_generated": 0,
                    "error": "No valid content found",
                }

            valid_log_ids, valid_contents = zip(*valid_pairs, strict=False)

            # Generate embeddings
            client = EmbeddingClient(settings)
            try:
                embeddings = await client.create_embeddings_batch(list(valid_contents))
            finally:
                await client.close()

            # Save embeddings to database
            saved_count = 0
            for log_id, embedding in zip(valid_log_ids, embeddings, strict=False):
                updated = await log_repo.update_embedding(log_id, embedding)
                if updated:
                    saved_count += 1

            await session.commit()

            return {
                "logs_processed": len(log_ids),
                "embeddings_generated": len(embeddings),
                "embeddings_saved": saved_count,
            }

    try:
        return run_async(_batch_embed())
    except Exception as e:
        logger.error(f"Failed to batch generate embeddings: {e}")
        return {"error": str(e), "logs_processed": 0}


@celery_app.task
def backfill_embeddings(batch_size: int = 50, max_logs: int = 500) -> dict:
    """
    Generate embeddings for logs that don't have them.

    Useful for backfilling embeddings for existing logs.
    """
    logger.info(f"Starting embedding backfill (batch_size={batch_size}, max={max_logs})")

    async def _backfill() -> dict:
        from sqlalchemy import select

        from app.infrastructure.database.models.log import Log

        session_factory = get_session_factory()
        async with session_factory() as session:
            # Find logs without embeddings that have content
            stmt = (
                select(Log.id)
                .where(Log.embedding.is_(None))
                .where((Log.error_content.isnot(None)) | (Log.log_content.isnot(None)))
                .limit(max_logs)
            )
            result = await session.execute(stmt)
            log_ids = [row[0] for row in result.fetchall()]

            if not log_ids:
                return {
                    "status": "no_logs_to_process",
                    "logs_found": 0,
                    "batches_queued": 0,
                }

            # Queue batch tasks
            batches_queued = 0
            for i in range(0, len(log_ids), batch_size):
                batch_ids = log_ids[i : i + batch_size]
                batch_generate_embeddings.delay(batch_ids)
                batches_queued += 1

            return {
                "status": "queued",
                "logs_found": len(log_ids),
                "batches_queued": batches_queued,
            }

    try:
        return run_async(_backfill())
    except Exception as e:
        logger.error(f"Failed to backfill embeddings: {e}")
        return {"error": str(e), "status": "failed"}


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
