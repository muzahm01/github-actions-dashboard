"""System language test framework parsers (Go, Rust, PHP, .NET)."""

from __future__ import annotations

import re

from app.application.services.parsers.base import BaseParser, TestResult


class GoTestParser(BaseParser):
    """Parser for Go test output."""

    # Patterns without ^ anchor to be more flexible
    PASS_PATTERN = re.compile(r"--- PASS:")
    FAIL_PATTERN = re.compile(r"--- FAIL:")
    SKIP_PATTERN = re.compile(r"--- SKIP:")
    RESULT_PATTERN = re.compile(r"(ok|FAIL)\s+\S+\s+([\d.]+)s")

    def can_parse(self, log_content: str) -> bool:
        """Check for Go test indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return (
            "--- PASS:" in content
            or "--- FAIL:" in content
            or "ok " in content
            or "FAIL\t" in content
        )

    def parse(self, log_content: str) -> TestResult | None:
        """Parse Go test output."""
        content = self.preprocess(log_content)

        passed = len(self.PASS_PATTERN.findall(content))
        failed = len(self.FAIL_PATTERN.findall(content))
        skipped = len(self.SKIP_PATTERN.findall(content))

        # Get duration from result line
        duration = None
        for match in self.RESULT_PATTERN.finditer(content):
            duration = float(match.group(2))

        return TestResult(
            framework="go-test",
            total=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


class CargoTestParser(BaseParser):
    """Parser for Rust cargo test output."""

    SUMMARY_PATTERN = re.compile(
        r"test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored"
    )
    TIME_PATTERN = re.compile(r"finished in ([\d.]+)s")

    def can_parse(self, log_content: str) -> bool:
        """Check for cargo test indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return "test result:" in content and "passed;" in content

    def parse(self, log_content: str) -> TestResult | None:
        """Parse cargo test output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        passed = int(match.group(1))
        failed = int(match.group(2))
        skipped = int(match.group(3))

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))

        return TestResult(
            framework="cargo-test",
            total=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


class PHPUnitParser(BaseParser):
    """Parser for PHPUnit output."""

    OK_PATTERN = re.compile(r"OK \((\d+) tests?, (\d+) assertions?\)")
    FAILURE_PATTERN = re.compile(
        r"Tests: (\d+), Assertions: (\d+)(?:, Failures: (\d+))?(?:, Errors: (\d+))?(?:, Skipped: (\d+))?"
    )
    TIME_PATTERN = re.compile(r"Time: ([\d.:]+)")

    def can_parse(self, log_content: str) -> bool:
        """Check for PHPUnit indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return ("OK (" in content and "tests" in content) or (
            "Tests:" in content and "Assertions:" in content
        )

    def parse(self, log_content: str) -> TestResult | None:
        """Parse PHPUnit output."""
        content = self.preprocess(log_content)

        # Try OK pattern first
        ok_match = self.OK_PATTERN.search(content)
        if ok_match:
            total = int(ok_match.group(1))
            return TestResult(
                framework="phpunit",
                total=total,
                passed=total,
                failed=0,
                skipped=0,
            )

        # Try failure pattern
        fail_match = self.FAILURE_PATTERN.search(content)
        if fail_match:
            total = int(fail_match.group(1))
            failures = int(fail_match.group(3)) if fail_match.group(3) else 0
            errors = int(fail_match.group(4)) if fail_match.group(4) else 0
            skipped = int(fail_match.group(5)) if fail_match.group(5) else 0
            failed = failures + errors

            return TestResult(
                framework="phpunit",
                total=total,
                passed=total - failed - skipped,
                failed=failed,
                skipped=skipped,
            )

        return None


class DotNetParser(BaseParser):
    """Parser for .NET test output."""

    SUMMARY_PATTERN = re.compile(
        r"(?:Passed!|Failed!)\s+-\s+Failed:\s+(\d+),\s+Passed:\s+(\d+),\s+Skipped:\s+(\d+),\s+Total:\s+(\d+)"
    )
    SIMPLE_PATTERN = re.compile(r"Total tests: (\d+)")
    TIME_PATTERN = re.compile(r"Duration: ([\d.]+) (ms|s)")

    def can_parse(self, log_content: str) -> bool:
        """Check for .NET test indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return ("Passed!" in content or "Failed!" in content) and "Total:" in content

    def parse(self, log_content: str) -> TestResult | None:
        """Parse .NET test output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        failed = int(match.group(1))
        passed = int(match.group(2))
        skipped = int(match.group(3))
        total = int(match.group(4))

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))
            if time_match.group(2) == "ms":
                duration /= 1000

        return TestResult(
            framework="dotnet",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )
