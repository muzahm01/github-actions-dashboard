"""Base types and classes for test result parsing."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class FailureDetail:
    """Details of a single test failure."""

    test_name: str
    error_message: str
    stack_trace: str | None = None
    file_path: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class TestResult:
    """Immutable test result value object."""

    framework: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float | None = None
    failures: list[FailureDetail] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100


class TestResultParser(Protocol):
    """Protocol for test result parsers."""

    def can_parse(self, log_content: str) -> bool:
        """Check if this parser can handle the log content."""
        ...

    def parse(self, log_content: str) -> TestResult | None:
        """Parse log content and extract test results."""
        ...


class BaseParser(ABC):
    """Base class for parsers with common utilities."""

    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove ANSI color codes from text."""
        ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
        return ansi_pattern.sub("", text)

    @staticmethod
    def strip_docker_noise(text: str) -> str:
        """Remove Docker container prefixes and timestamps."""
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove Docker timestamp prefixes like "2024-01-15T10:00:00.000Z "
            line = re.sub(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*Z?\s*", "", line)
            # Remove container name prefixes like "[container-name] "
            line = re.sub(r"^\[[\w-]+\]\s*", "", line)
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def preprocess(self, log_content: str) -> str:
        """Preprocess log content before parsing."""
        content = self.strip_ansi(log_content)
        content = self.strip_docker_noise(content)
        return content

    @abstractmethod
    def can_parse(self, log_content: str) -> bool:
        """Check if this parser can handle the log content."""
        ...

    @abstractmethod
    def parse(self, log_content: str) -> TestResult | None:
        """Parse log content and extract test results."""
        ...
