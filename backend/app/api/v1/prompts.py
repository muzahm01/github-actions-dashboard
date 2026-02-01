"""Custom prompt management API endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.application.services.prompt_service import (
    DEFAULT_PROMPTS,
    PromptService,
    PromptTemplate,
    PromptType,
)

router = APIRouter()

# Global prompt service instance
_prompt_service = PromptService()


class PromptTemplateCreate(BaseModel):
    """Request model for creating a prompt template."""

    name: str = Field(..., min_length=1, max_length=100)
    prompt_type: PromptType
    template: str = Field(..., min_length=10)
    description: str = ""
    variables: list[str] | None = None


class PromptTemplateUpdate(BaseModel):
    """Request model for updating a prompt template."""

    name: str | None = None
    template: str | None = None
    description: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


class PromptTemplateResponse(BaseModel):
    """Response model for a prompt template."""

    id: int
    name: str
    prompt_type: str
    template: str
    description: str
    variables: list[str]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RenderPromptRequest(BaseModel):
    """Request model for rendering a prompt."""

    prompt_type: PromptType
    prompt_id: int | None = None
    variables: dict[str, str]


class RenderPromptResponse(BaseModel):
    """Response model for rendered prompt."""

    rendered: str
    prompt_id: int
    prompt_name: str
    missing_variables: list[str]


def _to_response(prompt: PromptTemplate) -> PromptTemplateResponse:
    """Convert PromptTemplate to response model."""
    return PromptTemplateResponse(
        id=prompt.id,
        name=prompt.name,
        prompt_type=prompt.prompt_type.value,
        template=prompt.template,
        description=prompt.description,
        variables=prompt.variables,
        is_default=prompt.is_default,
        is_active=prompt.is_active,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.get("", response_model=list[PromptTemplateResponse])
async def list_prompts(
    prompt_type: PromptType | None = None,
    include_defaults: bool = True,
) -> list[PromptTemplateResponse]:
    """List all prompt templates."""
    prompts = await _prompt_service.list_prompts(
        prompt_type=prompt_type,
        include_defaults=include_defaults,
    )
    return [_to_response(p) for p in prompts]


@router.get("/types", response_model=list[dict])
async def list_prompt_types() -> list[dict]:
    """List all available prompt types."""
    return [
        {
            "type": pt.value,
            "has_default": pt in DEFAULT_PROMPTS,
            "description": DEFAULT_PROMPTS.get(
                pt, PromptTemplate(id=0, name="", prompt_type=pt, template="")
            ).description,
        }
        for pt in PromptType
    ]


@router.get("/{prompt_id}", response_model=PromptTemplateResponse)
async def get_prompt(prompt_id: int) -> PromptTemplateResponse:
    """Get a specific prompt template."""
    # Check defaults first
    for default in DEFAULT_PROMPTS.values():
        if default.id == prompt_id:
            return _to_response(default)

    # Check custom prompts
    for pt in PromptType:
        prompt = await _prompt_service.get_prompt(pt, prompt_id)
        if prompt.id == prompt_id:
            return _to_response(prompt)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Prompt with ID {prompt_id} not found",
    )


@router.post("", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(request: PromptTemplateCreate) -> PromptTemplateResponse:
    """Create a new custom prompt template."""
    prompt = await _prompt_service.create_prompt(
        name=request.name,
        prompt_type=request.prompt_type,
        template=request.template,
        description=request.description,
        variables=request.variables,
    )
    return _to_response(prompt)


@router.put("/{prompt_id}", response_model=PromptTemplateResponse)
async def update_prompt(
    prompt_id: int,
    request: PromptTemplateUpdate,
) -> PromptTemplateResponse:
    """Update an existing prompt template."""
    prompt = await _prompt_service.update_prompt(
        prompt_id=prompt_id,
        name=request.name,
        template=request.template,
        description=request.description,
        variables=request.variables,
        is_active=request.is_active,
    )

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found or cannot be modified",
        )

    return _to_response(prompt)


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_prompt(prompt_id: int) -> None:
    """Delete a custom prompt template."""
    deleted = await _prompt_service.delete_prompt(prompt_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found or cannot be deleted",
        )


@router.post("/render", response_model=RenderPromptResponse)
async def render_prompt(request: RenderPromptRequest) -> RenderPromptResponse:
    """Render a prompt template with provided variables."""
    prompt = await _prompt_service.get_prompt(
        request.prompt_type,
        request.prompt_id,
    )

    missing = prompt.validate_variables(request.variables)
    rendered = prompt.render(**request.variables)

    return RenderPromptResponse(
        rendered=rendered,
        prompt_id=prompt.id,
        prompt_name=prompt.name,
        missing_variables=missing,
    )


@router.get("/default/{prompt_type}", response_model=PromptTemplateResponse)
async def get_default_prompt(prompt_type: PromptType) -> PromptTemplateResponse:
    """Get the default prompt for a specific type."""
    prompt = _prompt_service.get_default_prompt(prompt_type)
    return _to_response(prompt)
