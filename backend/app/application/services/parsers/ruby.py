"""Ruby test framework parsers (RSpec, Minitest)."""

from __future__ import annotations

import re

from app.application.services.parsers.base import BaseParser, TestResult


class RSpecParser(BaseParser):
    """Parser for RSpec output."""

    SUMMARY_PATTERN = re.compile(r"(\d+) examples?, (\d+) failures?(?:, (\d+) pending)?")
    TIME_PATTERN = re.compile(r"Finished in ([\d.]+) seconds?")

    def can_parse(self, log_content: str) -> bool:
        """Check for RSpec indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return "examples" in content and "failures" in content

    def parse(self, log_content: str) -> TestResult | None:
        """Parse RSpec output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        total = int(match.group(1))
        failed = int(match.group(2))
        skipped = int(match.group(3)) if match.group(3) else 0
        passed = total - failed - skipped

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))

        return TestResult(
            framework="rspec",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


class MinitestParser(BaseParser):
    """Parser for Ruby Minitest output."""

    # Minitest output patterns
    SUMMARY_PATTERN = re.compile(
        r"(\d+) runs?, (\d+) assertions?, (\d+) failures?, (\d+) errors?, (\d+) skips?"
    )
    TIME_PATTERN = re.compile(r"Finished in ([\d.]+)(?:s| seconds?)")

    def can_parse(self, log_content: str) -> bool:
        """Check for Minitest indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return self.SUMMARY_PATTERN.search(content) is not None

    def parse(self, log_content: str) -> TestResult | None:
        """Parse Minitest output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        total = int(match.group(1))
        # assertions = int(match.group(2))  # Not used in TestResult
        failures = int(match.group(3))
        errors = int(match.group(4))
        skipped = int(match.group(5))

        failed = failures + errors
        passed = total - failed - skipped

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))

        return TestResult(
            framework="minitest",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )
