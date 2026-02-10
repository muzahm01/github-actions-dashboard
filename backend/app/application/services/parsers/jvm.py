"""JVM test framework parsers (JUnit, TestNG)."""

from __future__ import annotations

import re

from app.application.services.parsers.base import BaseParser, TestResult


class JUnitParser(BaseParser):
    """Parser for Java JUnit output (Maven/Gradle)."""

    SUMMARY_PATTERN = re.compile(
        r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)"
    )
    TIME_PATTERN = re.compile(r"Time elapsed: ([\d.]+) s")

    def can_parse(self, log_content: str) -> bool:
        """Check for JUnit indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return "Tests run:" in content and "Failures:" in content

    def parse(self, log_content: str) -> TestResult | None:
        """Parse JUnit output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        total = int(match.group(1))
        failures = int(match.group(2))
        errors = int(match.group(3))
        skipped = int(match.group(4))
        failed = failures + errors
        passed = total - failed - skipped

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))

        return TestResult(
            framework="junit",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


class TestNGParser(BaseParser):
    """Parser for Java TestNG output."""

    # TestNG output patterns
    SUMMARY_PATTERN = re.compile(
        r"Total tests run: (\d+), (?:Passes: (\d+), )?Failures: (\d+), Skips: (\d+)"
    )
    ALT_PATTERN = re.compile(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)")
    TIME_PATTERN = re.compile(r"Total time: ([\d.]+) seconds?")
    TESTNG_INDICATOR = re.compile(r"testng|TestNG")

    def can_parse(self, log_content: str) -> bool:
        """Check for TestNG indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return self.TESTNG_INDICATOR.search(content) is not None and (
            self.SUMMARY_PATTERN.search(content) is not None
            or self.ALT_PATTERN.search(content) is not None
        )

    def parse(self, log_content: str) -> TestResult | None:
        """Parse TestNG output."""
        content = self.preprocess(log_content)

        # Try main summary pattern first
        match = self.SUMMARY_PATTERN.search(content)
        if match:
            total = int(match.group(1))
            passed = int(match.group(2)) if match.group(2) else 0
            failed = int(match.group(3))
            skipped = int(match.group(4))
            if not passed:
                passed = total - failed - skipped
        else:
            # Try alternative pattern
            match = self.ALT_PATTERN.search(content)
            if not match:
                return None
            total = int(match.group(1))
            failures = int(match.group(2))
            errors = int(match.group(3))
            skipped = int(match.group(4))
            failed = failures + errors
            passed = total - failed - skipped

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))

        return TestResult(
            framework="testng",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )
