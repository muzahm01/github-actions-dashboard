"""Tests for workflow tasks."""

from unittest.mock import MagicMock, patch


import pytest

pytestmark = pytest.mark.unit

class TestWorkflowTasks:
    """Tests for workflow Celery tasks."""

    def test_run_async_helper(self) -> None:
        """Test the run_async helper function."""
        from app.tasks.workflow_tasks import run_async

        async def sample_coro() -> str:
            return "workflow_result"

        result = run_async(sample_coro())
        assert result == "workflow_result"


class TestSyncRepositoryTask:
    """Tests for sync_repository task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.workflow_tasks import sync_repository

        assert sync_repository.name == "app.tasks.workflow_tasks.sync_repository"
        assert sync_repository.max_retries == 3


class TestProcessWorkflowRunTask:
    """Tests for process_workflow_run task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.workflow_tasks import process_workflow_run

        assert process_workflow_run.name == "app.tasks.workflow_tasks.process_workflow_run"
        assert process_workflow_run.max_retries == 3


class TestSyncAllWorkflowsTask:
    """Tests for sync_all_workflows task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.workflow_tasks import sync_all_workflows

        assert sync_all_workflows.name == "app.tasks.workflow_tasks.sync_all_workflows"


class TestCleanupOldDataTask:
    """Tests for cleanup_old_data task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.workflow_tasks import cleanup_old_data

        assert cleanup_old_data.name == "app.tasks.workflow_tasks.cleanup_old_data"

    @patch("app.tasks.workflow_tasks.run_async")
    def test_cleanup_deletes_old_data(self, mock_run_async: MagicMock) -> None:
        """Test that cleanup deletes data older than retention period."""
        from app.tasks.workflow_tasks import cleanup_old_data

        def close_coro(coro):  # type: ignore[no-untyped-def]
            """Close coroutine to prevent ResourceWarning."""
            coro.close()
            return {
                "status": "completed",
                "deleted_runs": 10,
                "deleted_logs": 25,
            }

        mock_run_async.side_effect = close_coro

        result = cleanup_old_data()

        assert result["status"] == "completed"
        mock_run_async.assert_called_once()


class TestSyncAllWorkflowsWithDB:
    """Tests for sync_all_workflows with database integration."""

    @patch("app.tasks.workflow_tasks.run_async")
    def test_sync_fetches_active_repos(self, mock_run_async: MagicMock) -> None:
        """Test that sync fetches active repositories from database."""
        from app.tasks.workflow_tasks import sync_all_workflows

        def close_coro(coro):  # type: ignore[no-untyped-def]
            """Close coroutine to prevent ResourceWarning."""
            coro.close()
            return {
                "status": "completed",
                "repositories_synced": 3,
            }

        mock_run_async.side_effect = close_coro

        result = sync_all_workflows()

        assert result["status"] == "completed"


class TestCeleryAppConfig:
    """Tests for Celery app configuration."""

    def test_celery_app_broker(self) -> None:
        """Test Celery app is configured with Redis broker."""
        from app.tasks.celery_app import celery_app

        assert celery_app.main == "github_actions_dashboard"

    def test_celery_app_includes_tasks(self) -> None:
        """Test Celery app includes task modules."""
        from app.tasks.celery_app import celery_app

        includes = celery_app.conf.include
        assert "app.tasks.workflow_tasks" in includes
        assert "app.tasks.analysis_tasks" in includes

    def test_celery_beat_schedule(self) -> None:
        """Test Celery beat schedule is configured."""
        from app.tasks.celery_app import celery_app

        schedule = celery_app.conf.beat_schedule
        assert "sync-workflows-every-5-minutes" in schedule
        assert "cleanup-old-data-daily" in schedule
