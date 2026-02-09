"""Custom prompt management service."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of analysis prompts."""

    ERROR_ANALYSIS = "error_analysis"
    TEST_FAILURE = "test_failure"
    BUILD_FAILURE = "build_failure"
    DEPLOYMENT_FAILURE = "deployment_failure"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    SUMMARY = "summary"


@dataclass
class PromptTemplate:
    """Custom prompt template."""

    id: int
    name: str
    prompt_type: PromptType
    template: str
    description: str = ""
    variables: list[str] = field(default_factory=list)
    is_default: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def render(self, **kwargs: str) -> str:
        """Render template with provided variables."""
        result = self.template
        for var in self.variables:
            placeholder = f"{{{var}}}"
            value = kwargs.get(var, "")
            result = result.replace(placeholder, str(value))
        return result

    def validate_variables(self, provided: dict[str, Any]) -> list[str]:
        """Validate that all required variables are provided.

        Returns list of missing variables.
        """
        missing = []
        for var in self.variables:
            if var not in provided or not provided[var]:
                missing.append(var)
        return missing


# Default prompt templates
DEFAULT_PROMPTS: dict[PromptType, PromptTemplate] = {
    PromptType.ERROR_ANALYSIS: PromptTemplate(
        id=1,
        name="Default Error Analysis",
        prompt_type=PromptType.ERROR_ANALYSIS,
        description="Standard error analysis prompt for CI/CD failures",
        template="""You are an expert CI/CD debugger analyzing a GitHub Actions workflow failure.

Analyze the following error log and provide:
1. Root cause analysis - what went wrong and why
2. A brief error summary (1-2 sentences)
3. Suggested fixes (actionable steps to resolve)
4. Prevention tips (how to avoid this in the future)
5. Confidence score (0.0 to 1.0) based on how certain you are
6. Related documentation links if applicable

Error Log:
```
{log_content}
```

Test Framework: {framework}
Job Name: {job_name}

Respond in this exact JSON format:
{{
    "root_cause": "detailed explanation of what caused the error",
    "error_summary": "brief 1-2 sentence summary",
    "suggested_fixes": ["fix 1", "fix 2", ...],
    "prevention_tips": ["tip 1", "tip 2", ...],
    "confidence_score": 0.85,
    "related_documentation": ["https://docs.example.com/..."]
}}

Only respond with valid JSON, no additional text.""",
        variables=["log_content", "framework", "job_name"],
        is_default=True,
    ),
    PromptType.TEST_FAILURE: PromptTemplate(
        id=2,
        name="Test Failure Analysis",
        prompt_type=PromptType.TEST_FAILURE,
        description="Specialized prompt for test failure analysis",
        template="""You are an expert software tester analyzing test failures.

Analyze the following test failure output:

Framework: {framework}
Test Output:
```
{log_content}
```

Failed Tests:
{failed_tests}

Please provide:
1. Root cause of the test failures
2. Common patterns across failures (if multiple)
3. Suggested code fixes
4. Test improvement suggestions
5. Confidence score (0.0 to 1.0)

Respond in JSON format:
{{
    "root_cause": "explanation",
    "error_summary": "brief summary",
    "patterns": ["pattern 1", "pattern 2"],
    "suggested_fixes": ["fix 1", "fix 2"],
    "test_improvements": ["improvement 1", "improvement 2"],
    "confidence_score": 0.85
}}""",
        variables=["log_content", "framework", "failed_tests"],
        is_default=True,
    ),
    PromptType.BUILD_FAILURE: PromptTemplate(
        id=3,
        name="Build Failure Analysis",
        prompt_type=PromptType.BUILD_FAILURE,
        description="Specialized prompt for build/compilation failures",
        template="""You are an expert build engineer analyzing a build failure.

Build System: {build_system}
Build Log:
```
{log_content}
```

Please analyze this build failure and provide:
1. Root cause of the build failure
2. Specific file(s) and line(s) causing the issue
3. Step-by-step fix instructions
4. Prevention recommendations
5. Confidence score (0.0 to 1.0)

Respond in JSON format:
{{
    "root_cause": "explanation",
    "error_summary": "brief summary",
    "affected_files": ["{{"file": "path", "line": 123, "issue": "description"}}"],
    "suggested_fixes": ["fix 1", "fix 2"],
    "prevention_tips": ["tip 1", "tip 2"],
    "confidence_score": 0.85
}}""",
        variables=["log_content", "build_system"],
        is_default=True,
    ),
    PromptType.DEPLOYMENT_FAILURE: PromptTemplate(
        id=4,
        name="Deployment Failure Analysis",
        prompt_type=PromptType.DEPLOYMENT_FAILURE,
        description="Specialized prompt for deployment failures",
        template="""You are an expert DevOps engineer analyzing a deployment failure.

Deployment Target: {deployment_target}
Environment: {environment}
Deployment Log:
```
{log_content}
```

Please analyze this deployment failure and provide:
1. Root cause of the deployment failure
2. Infrastructure or configuration issues identified
3. Rollback recommendations (if applicable)
4. Step-by-step remediation
5. Prevention strategies
6. Confidence score (0.0 to 1.0)

Respond in JSON format:
{{
    "root_cause": "explanation",
    "error_summary": "brief summary",
    "infrastructure_issues": ["issue 1", "issue 2"],
    "rollback_needed": true/false,
    "rollback_steps": ["step 1", "step 2"],
    "suggested_fixes": ["fix 1", "fix 2"],
    "prevention_tips": ["tip 1", "tip 2"],
    "confidence_score": 0.85
}}""",
        variables=["log_content", "deployment_target", "environment"],
        is_default=True,
    ),
    PromptType.SUMMARY: PromptTemplate(
        id=5,
        name="Failure Summary",
        prompt_type=PromptType.SUMMARY,
        description="Summarize multiple failures",
        template="""Summarize these test failures in 2-3 sentences, identifying common patterns:

{failures_text}

Provide a concise summary focusing on the main issues.""",
        variables=["failures_text"],
        is_default=True,
    ),
}


class PromptStore(Protocol):
    """Protocol for prompt persistence."""

    async def get_by_id(self, prompt_id: int) -> PromptTemplate | None:
        """Get prompt by ID."""
        ...

    async def get_by_type(self, prompt_type: PromptType) -> list[PromptTemplate]:
        """Get prompts by type."""
        ...

    async def get_active_by_type(self, prompt_type: PromptType) -> PromptTemplate | None:
        """Get active prompt for type."""
        ...

    async def save(self, prompt: PromptTemplate) -> PromptTemplate:
        """Save prompt."""
        ...

    async def delete(self, prompt_id: int) -> bool:
        """Delete prompt."""
        ...


class PromptService:
    """Service for managing custom analysis prompts."""

    def __init__(self, store: PromptStore | None = None) -> None:
        """Initialize prompt service."""
        self._store = store
        # In-memory cache of custom prompts
        self._custom_prompts: dict[int, PromptTemplate] = {}

    async def get_prompt(
        self,
        prompt_type: PromptType,
        prompt_id: int | None = None,
    ) -> PromptTemplate:
        """Get prompt by type or specific ID.

        Falls back to default if no custom prompt is found.
        """
        # If specific ID requested, try to get it
        if prompt_id:
            if self._store:
                prompt = await self._store.get_by_id(prompt_id)
                if prompt:
                    return prompt
            elif prompt_id in self._custom_prompts:
                return self._custom_prompts[prompt_id]

        # Try to get active custom prompt for type
        if self._store:
            prompt = await self._store.get_active_by_type(prompt_type)
            if prompt:
                return prompt
        else:
            # Check in-memory custom prompts
            for prompt in self._custom_prompts.values():
                if prompt.prompt_type == prompt_type and prompt.is_active:
                    return prompt

        # Fall back to default
        return DEFAULT_PROMPTS.get(
            prompt_type,
            DEFAULT_PROMPTS[PromptType.ERROR_ANALYSIS],
        )

    async def list_prompts(
        self,
        prompt_type: PromptType | None = None,
        include_defaults: bool = True,
    ) -> list[PromptTemplate]:
        """List all prompts, optionally filtered by type."""
        prompts = []

        # Add defaults if requested
        if include_defaults:
            for default_prompt in DEFAULT_PROMPTS.values():
                if prompt_type is None or default_prompt.prompt_type == prompt_type:
                    prompts.append(default_prompt)

        # Add custom prompts
        if self._store:
            if prompt_type:
                custom = await self._store.get_by_type(prompt_type)
            else:
                custom = []
                for pt in PromptType:
                    custom.extend(await self._store.get_by_type(pt))
            prompts.extend(custom)
        else:
            for prompt in self._custom_prompts.values():
                if prompt_type is None or prompt.prompt_type == prompt_type:
                    prompts.append(prompt)

        return prompts

    async def create_prompt(
        self,
        name: str,
        prompt_type: PromptType,
        template: str,
        description: str = "",
        variables: list[str] | None = None,
    ) -> PromptTemplate:
        """Create a new custom prompt."""
        # Auto-detect variables from template
        if variables is None:
            import re

            variables = list(dict.fromkeys(re.findall(r"\{(\w+)\}", template)))

        prompt = PromptTemplate(
            id=len(self._custom_prompts) + 100,  # Start custom IDs at 100
            name=name,
            prompt_type=prompt_type,
            template=template,
            description=description,
            variables=variables,
            is_default=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        if self._store:
            prompt = await self._store.save(prompt)
        else:
            self._custom_prompts[prompt.id] = prompt

        logger.info(f"Created custom prompt: {prompt.name} ({prompt.id})")
        return prompt

    async def update_prompt(
        self,
        prompt_id: int,
        name: str | None = None,
        template: str | None = None,
        description: str | None = None,
        variables: list[str] | None = None,
        is_active: bool | None = None,
    ) -> PromptTemplate | None:
        """Update an existing prompt."""
        # Get existing prompt
        prompt = None
        if self._store:
            prompt = await self._store.get_by_id(prompt_id)
        elif prompt_id in self._custom_prompts:
            prompt = self._custom_prompts[prompt_id]

        if not prompt:
            return None

        # Cannot modify default prompts
        if prompt.is_default:
            logger.warning(f"Cannot modify default prompt: {prompt_id}")
            return None

        # Apply updates
        if name is not None:
            prompt.name = name
        if template is not None:
            prompt.template = template
        if description is not None:
            prompt.description = description
        if variables is not None:
            prompt.variables = variables
        if is_active is not None:
            prompt.is_active = is_active

        prompt.updated_at = datetime.utcnow()

        # Save
        if self._store:
            prompt = await self._store.save(prompt)
        else:
            self._custom_prompts[prompt_id] = prompt

        logger.info(f"Updated prompt: {prompt.name} ({prompt.id})")
        return prompt

    async def delete_prompt(self, prompt_id: int) -> bool:
        """Delete a custom prompt."""
        # Cannot delete default prompts
        if prompt_id < 100:
            logger.warning(f"Cannot delete default prompt: {prompt_id}")
            return False

        if self._store:
            return await self._store.delete(prompt_id)
        elif prompt_id in self._custom_prompts:
            del self._custom_prompts[prompt_id]
            logger.info(f"Deleted prompt: {prompt_id}")
            return True

        return False

    async def render_prompt(
        self,
        prompt_type: PromptType,
        variables: dict[str, Any],
        prompt_id: int | None = None,
    ) -> str:
        """Render a prompt with provided variables."""
        prompt = await self.get_prompt(prompt_type, prompt_id)

        # Validate variables
        missing = prompt.validate_variables(variables)
        if missing:
            logger.warning(f"Missing variables for prompt: {missing}")

        return prompt.render(**variables)

    def get_default_prompt(self, prompt_type: PromptType) -> PromptTemplate:
        """Get default prompt for a type."""
        return DEFAULT_PROMPTS.get(
            prompt_type,
            DEFAULT_PROMPTS[PromptType.ERROR_ANALYSIS],
        )
