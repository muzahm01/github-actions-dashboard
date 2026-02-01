"""TestResult domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

TestFramework = Literal[
    "pytest",
    "unittest",
    "nose2",  # Python
    "jest",
    "mocha",
    "vitest",
    "playwright",  # JavaScript
    "go_test",  # Go
    "rspec",
    "minitest",  # Ruby
    "xunit",
    "nunit",
    "mstest",  # .NET
    "junit",
    "testng",  # Java
    "cargo_test",  # Rust
    "phpunit",  # PHP
    "unknown",
]


@dataclass
class TestFailure:
    """Individual test failure details."""

    test_name: str
    error_message: str
    stack_trace: str = ""
    file_path: str = ""
    line_number: int | None = None


@dataclass
class TestResult:
    """Domain entity representing parsed test results."""

    id: int
    log_id: int
    framework: TestFramework
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float = 0.0
    failures: list[TestFailure] = field(default_factory=list)
    raw_output: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        log_id: int,
        framework: TestFramework,
        total_tests: int,
        passed: int,
        failed: int,
        skipped: int,
        duration_seconds: float = 0.0,
        failures: list[TestFailure] | None = None,
    ) -> TestResult:
        """Create a new test result entity."""
        return cls(
            id=0,
            log_id=log_id,
            framework=framework,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration_seconds,
            failures=failures or [],
            created_at=datetime.utcnow(),
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    def is_passing(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0

    def has_failures(self) -> bool:
        """Check if there are any failures."""
        return self.failed > 0

    @property
    def failure_count(self) -> int:
        """Get number of failed tests."""
        return self.failed

    def get_failure_summary(self, max_failures: int = 5) -> str:
        """Get summary of failures for display."""
        if not self.failures:
            return "No failure details available"

        summary_parts = []
        for failure in self.failures[:max_failures]:
            summary_parts.append(f"- {failure.test_name}: {failure.error_message[:100]}")

        if len(self.failures) > max_failures:
            summary_parts.append(f"... and {len(self.failures) - max_failures} more failures")

        return "\n".join(summary_parts)
