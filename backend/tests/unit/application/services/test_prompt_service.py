"""Unit tests for prompt_service."""

import pytest

from app.application.services.prompt_service import (
    DEFAULT_PROMPTS,
    PromptService,
    PromptTemplate,
    PromptType,
)


@pytest.fixture()
def service() -> PromptService:
    """Create a prompt service with in-memory storage."""
    return PromptService()


@pytest.mark.unit
class TestPromptTemplate:
    """Tests for PromptTemplate dataclass."""

    def test_render_replaces_variables(self) -> None:
        template = PromptTemplate(
            id=100,
            name="test",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="Error: {error}\nJob: {job}",
            variables=["error", "job"],
        )
        result = template.render(error="NullPointer", job="build")
        assert result == "Error: NullPointer\nJob: build"

    def test_render_missing_variable_becomes_empty(self) -> None:
        template = PromptTemplate(
            id=100,
            name="test",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="Error: {error}",
            variables=["error"],
        )
        result = template.render()
        assert result == "Error: "

    def test_validate_variables_reports_missing(self) -> None:
        template = PromptTemplate(
            id=100,
            name="test",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="{a} {b}",
            variables=["a", "b"],
        )
        missing = template.validate_variables({"a": "value"})
        assert missing == ["b"]

    def test_validate_variables_all_provided(self) -> None:
        template = PromptTemplate(
            id=100,
            name="test",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="{x}",
            variables=["x"],
        )
        missing = template.validate_variables({"x": "val"})
        assert missing == []

    def test_success_rate_property(self) -> None:
        from app.application.services.parsers.base import TestResult

        result = TestResult(framework="pytest", total=10, passed=8, failed=1, skipped=1)
        assert result.success_rate == 80.0


@pytest.mark.unit
class TestPromptService:
    """Tests for PromptService."""

    async def test_get_prompt_returns_default(self, service: PromptService) -> None:
        prompt = await service.get_prompt(PromptType.ERROR_ANALYSIS)
        assert prompt is not None
        assert prompt.is_default is True
        assert prompt.prompt_type == PromptType.ERROR_ANALYSIS

    async def test_list_prompts_includes_defaults(self, service: PromptService) -> None:
        prompts = await service.list_prompts()
        assert len(prompts) >= len(DEFAULT_PROMPTS)

    async def test_list_prompts_filter_by_type(self, service: PromptService) -> None:
        prompts = await service.list_prompts(prompt_type=PromptType.TEST_FAILURE)
        assert all(p.prompt_type == PromptType.TEST_FAILURE for p in prompts)

    async def test_create_prompt(self, service: PromptService) -> None:
        prompt = await service.create_prompt(
            name="Custom",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="Analyze: {log_content}",
            description="Custom prompt",
            variables=["log_content"],
        )
        assert prompt.name == "Custom"
        assert prompt.is_default is False
        assert prompt.is_active is True

    async def test_update_prompt(self, service: PromptService) -> None:
        prompt = await service.create_prompt(
            name="Original",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="old template",
        )
        updated = await service.update_prompt(prompt.id, name="Updated")
        assert updated is not None
        assert updated.name == "Updated"

    async def test_update_default_prompt_fails(self, service: PromptService) -> None:
        result = await service.update_prompt(1, name="Hacked")
        assert result is None

    async def test_delete_prompt(self, service: PromptService) -> None:
        prompt = await service.create_prompt(
            name="ToDelete",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="temp",
        )
        deleted = await service.delete_prompt(prompt.id)
        assert deleted is True

    async def test_delete_default_prompt_fails(self, service: PromptService) -> None:
        deleted = await service.delete_prompt(1)
        assert deleted is False

    async def test_get_prompt_prefers_custom_over_default(
        self, service: PromptService
    ) -> None:
        await service.create_prompt(
            name="Custom Error",
            prompt_type=PromptType.ERROR_ANALYSIS,
            template="custom {log_content}",
            variables=["log_content"],
        )
        prompt = await service.get_prompt(PromptType.ERROR_ANALYSIS)
        assert prompt.name == "Custom Error"
        assert prompt.is_default is False

    async def test_render_prompt(self, service: PromptService) -> None:
        rendered = await service.render_prompt(
            PromptType.ERROR_ANALYSIS,
            variables={
                "log_content": "error here",
                "framework": "pytest",
                "job_name": "test-job",
            },
        )
        assert "error here" in rendered
        assert "pytest" in rendered
