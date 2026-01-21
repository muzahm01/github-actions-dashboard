"""Multi-framework test result parser."""

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


class PytestParser(BaseParser):
    """Parser for pytest output."""

    # Patterns for pytest output - more flexible matching
    COLLECTED_PATTERN = re.compile(r"collected (\d+) items?")
    FAILURE_PATTERN = re.compile(r"_{5,} (?P<test_name>[\w\[\]._-]+) _{5,}", re.MULTILINE)

    # Individual count patterns for more flexible matching
    PASSED_PATTERN = re.compile(r"(\d+) passed")
    FAILED_PATTERN = re.compile(r"(\d+) failed")
    ERROR_PATTERN = re.compile(r"(\d+) error")
    SKIPPED_PATTERN = re.compile(r"(\d+) skipped")
    XFAILED_PATTERN = re.compile(r"(\d+) xfailed")
    DURATION_PATTERN = re.compile(r"in ([\d.]+)s")
    SUMMARY_LINE_PATTERN = re.compile(r"[=]{3,}.*[=]{3,}")

    def can_parse(self, log_content: str) -> bool:
        """Check for pytest indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        has_collected = self.COLLECTED_PATTERN.search(content) is not None
        has_summary = self.SUMMARY_LINE_PATTERN.search(content) is not None
        has_pytest_terms = any(term in content for term in ["passed", "failed", "error", "pytest"])
        return has_collected or (has_summary and has_pytest_terms)

    def parse(self, log_content: str) -> TestResult | None:
        """Parse pytest output."""
        content = self.preprocess(log_content)

        # Extract counts using individual patterns
        passed_match = self.PASSED_PATTERN.search(content)
        failed_match = self.FAILED_PATTERN.search(content)
        error_match = self.ERROR_PATTERN.search(content)
        skipped_match = self.SKIPPED_PATTERN.search(content)
        xfailed_match = self.XFAILED_PATTERN.search(content)
        duration_match = self.DURATION_PATTERN.search(content)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        errors = int(error_match.group(1)) if error_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        xfailed = int(xfailed_match.group(1)) if xfailed_match else 0
        duration = float(duration_match.group(1)) if duration_match else None

        # Combine errors into failed, xfailed into skipped
        failed = failed + errors
        skipped = skipped + xfailed

        # Check if we got any counts - if all zero and no summary line, return None
        if (
            passed == 0
            and failed == 0
            and skipped == 0
            and not self.SUMMARY_LINE_PATTERN.search(content)
        ):
            return None

        # Extract total from collected
        collected_match = self.COLLECTED_PATTERN.search(content)
        total = int(collected_match.group(1)) if collected_match else passed + failed + skipped

        # Extract failure details
        failures = self._extract_failures(content)

        return TestResult(
            framework="pytest",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
            failures=failures,
        )

    def _extract_failures(self, content: str) -> list[FailureDetail]:
        """Extract failure details from pytest output."""
        failures = []
        for match in self.FAILURE_PATTERN.finditer(content):
            test_name = match.group("test_name")
            # Find the error message after this header
            start = match.end()
            next_match = self.FAILURE_PATTERN.search(content, start)
            end = next_match.start() if next_match else len(content)
            error_block = content[start:end]

            # Extract error message (first line after "E ")
            error_lines = [line[2:] for line in error_block.split("\n") if line.startswith("E ")]
            error_message = "\n".join(error_lines) if error_lines else "Unknown error"

            failures.append(
                FailureDetail(
                    test_name=test_name,
                    error_message=error_message[:500],  # Truncate
                    stack_trace=error_block[:2000] if len(error_block) > 0 else None,
                )
            )

        return failures


class JestParser(BaseParser):
    """Parser for Jest output."""

    SUMMARY_PATTERN = re.compile(
        r"Tests:\s+(?:(?P<failed>\d+) failed,?\s*)?"
        r"(?:(?P<skipped>\d+) skipped,?\s*)?"
        r"(?:(?P<passed>\d+) passed,?\s*)?"
        r"(?P<total>\d+) total"
    )
    TIME_PATTERN = re.compile(r"Time:\s+([\d.]+)\s*s")

    def can_parse(self, log_content: str) -> bool:
        """Check for Jest indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return "Tests:" in content and ("passed" in content or "failed" in content)

    def parse(self, log_content: str) -> TestResult | None:
        """Parse Jest output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        groups = match.groupdict()
        time_match = self.TIME_PATTERN.search(content)

        return TestResult(
            framework="jest",
            total=int(groups.get("total") or 0),
            passed=int(groups.get("passed") or 0),
            failed=int(groups.get("failed") or 0),
            skipped=int(groups.get("skipped") or 0),
            duration_seconds=float(time_match.group(1)) if time_match else None,
        )


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


class MochaParser(BaseParser):
    """Parser for Mocha output."""

    SUMMARY_PATTERN = re.compile(r"(\d+) passing.*?(?:(\d+) failing)?.*?(?:(\d+) pending)?")
    TIME_PATTERN = re.compile(r"\((\d+(?:\.\d+)?)(ms|s)\)")

    def can_parse(self, log_content: str) -> bool:
        """Check for Mocha indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return "passing" in content and (
            "failing" in content or "pending" in content or ")" in content
        )

    def parse(self, log_content: str) -> TestResult | None:
        """Parse Mocha output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        passed = int(match.group(1)) if match.group(1) else 0
        failed = int(match.group(2)) if match.group(2) else 0
        skipped = int(match.group(3)) if match.group(3) else 0

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))
            if time_match.group(2) == "ms":
                duration /= 1000

        return TestResult(
            framework="mocha",
            total=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


class VitestParser(BaseParser):
    """Parser for Vitest output."""

    SUMMARY_PATTERN = re.compile(
        r"Tests\s+(?:(?P<failed>\d+) failed\s*\|\s*)?"
        r"(?:(?P<skipped>\d+) skipped\s*\|\s*)?"
        r"(?P<passed>\d+) passed"
    )
    TOTAL_PATTERN = re.compile(r"\((\d+)\)")
    TIME_PATTERN = re.compile(r"Duration\s+([\d.]+)\s*s")

    def can_parse(self, log_content: str) -> bool:
        """Check for Vitest indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return "Tests" in content and "passed" in content and "|" in content

    def parse(self, log_content: str) -> TestResult | None:
        """Parse Vitest output."""
        content = self.preprocess(log_content)

        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None

        groups = match.groupdict()
        passed = int(groups.get("passed") or 0)
        failed = int(groups.get("failed") or 0)
        skipped = int(groups.get("skipped") or 0)

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))

        return TestResult(
            framework="vitest",
            total=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


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


class UnittestParser(BaseParser):
    """Parser for Python unittest output."""

    # unittest output patterns
    OK_PATTERN = re.compile(r"^OK$", re.MULTILINE)
    FAILED_PATTERN = re.compile(r"^FAILED \(.*\)$", re.MULTILINE)
    RAN_PATTERN = re.compile(r"Ran (\d+) tests? in ([\d.]+)s")
    FAILURES_PATTERN = re.compile(r"failures?=(\d+)")
    ERRORS_PATTERN = re.compile(r"errors?=(\d+)")
    SKIPPED_PATTERN = re.compile(r"skipped=(\d+)")

    def can_parse(self, log_content: str) -> bool:
        """Check for unittest indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return self.RAN_PATTERN.search(content) is not None and (
            "OK" in content or "FAILED" in content
        )

    def parse(self, log_content: str) -> TestResult | None:
        """Parse unittest output."""
        content = self.preprocess(log_content)

        ran_match = self.RAN_PATTERN.search(content)
        if not ran_match:
            return None

        total = int(ran_match.group(1))
        duration = float(ran_match.group(2))

        failures = 0
        errors = 0
        skipped = 0

        failures_match = self.FAILURES_PATTERN.search(content)
        if failures_match:
            failures = int(failures_match.group(1))

        errors_match = self.ERRORS_PATTERN.search(content)
        if errors_match:
            errors = int(errors_match.group(1))

        skipped_match = self.SKIPPED_PATTERN.search(content)
        if skipped_match:
            skipped = int(skipped_match.group(1))

        failed = failures + errors
        passed = total - failed - skipped

        return TestResult(
            framework="unittest",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


class Nose2Parser(BaseParser):
    """Parser for Python nose2 output."""

    # nose2 output patterns
    RAN_PATTERN = re.compile(r"Ran (\d+) tests? in ([\d.]+)s")
    OK_PATTERN = re.compile(r"^OK$", re.MULTILINE)
    FAILED_PATTERN = re.compile(r"^FAILED", re.MULTILINE)
    FAILURES_PATTERN = re.compile(r"failures?=(\d+)")
    ERRORS_PATTERN = re.compile(r"errors?=(\d+)")
    SKIPPED_PATTERN = re.compile(r"skipped=(\d+)")
    NOSE2_INDICATOR = re.compile(r"nose2|\.\.\.+")

    def can_parse(self, log_content: str) -> bool:
        """Check for nose2 indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        # nose2 output is similar to unittest but may have nose2 specific markers
        has_ran = self.RAN_PATTERN.search(content) is not None
        has_dots = re.search(r"^[.FEsxX]+$", content, re.MULTILINE) is not None
        return has_ran and has_dots and "nose2" in content.lower()

    def parse(self, log_content: str) -> TestResult | None:
        """Parse nose2 output."""
        content = self.preprocess(log_content)

        ran_match = self.RAN_PATTERN.search(content)
        if not ran_match:
            return None

        total = int(ran_match.group(1))
        duration = float(ran_match.group(2))

        failures = 0
        errors = 0
        skipped = 0

        failures_match = self.FAILURES_PATTERN.search(content)
        if failures_match:
            failures = int(failures_match.group(1))

        errors_match = self.ERRORS_PATTERN.search(content)
        if errors_match:
            errors = int(errors_match.group(1))

        skipped_match = self.SKIPPED_PATTERN.search(content)
        if skipped_match:
            skipped = int(skipped_match.group(1))

        failed = failures + errors
        passed = total - failed - skipped

        return TestResult(
            framework="nose2",
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


class PlaywrightParser(BaseParser):
    """Parser for Playwright test output."""

    # Playwright output patterns
    SUMMARY_PATTERN = re.compile(r"(\d+) passed(?:.*?(\d+) failed)?(?:.*?(\d+) skipped)?")
    ALT_PATTERN = re.compile(
        r"(\d+) (?:test|spec)s? (?:passed|total)(?:.*?(\d+) failed)?(?:.*?(\d+) skipped)?"
    )
    TIME_PATTERN = re.compile(r"\(([\d.]+)(?:s|ms)\)")
    PLAYWRIGHT_INDICATOR = re.compile(r"playwright|Running \d+ tests?|chromium|firefox|webkit")

    def can_parse(self, log_content: str) -> bool:
        """Check for Playwright indicators."""
        if not log_content:
            return False
        content = self.preprocess(log_content)
        return self.PLAYWRIGHT_INDICATOR.search(content) is not None and (
            self.SUMMARY_PATTERN.search(content) is not None or "passed" in content
        )

    def parse(self, log_content: str) -> TestResult | None:
        """Parse Playwright output."""
        content = self.preprocess(log_content)

        # Try main pattern
        match = self.SUMMARY_PATTERN.search(content)
        if match:
            passed = int(match.group(1))
            failed = int(match.group(2)) if match.group(2) else 0
            skipped = int(match.group(3)) if match.group(3) else 0
        else:
            # Try alternative pattern
            match = self.ALT_PATTERN.search(content)
            if not match:
                return None
            passed = int(match.group(1))
            failed = int(match.group(2)) if match.group(2) else 0
            skipped = int(match.group(3)) if match.group(3) else 0

        total = passed + failed + skipped

        # Get duration
        duration = None
        time_match = self.TIME_PATTERN.search(content)
        if time_match:
            duration = float(time_match.group(1))
            # Check if it's in milliseconds
            if "ms" in content[time_match.start() : time_match.end() + 5]:
                duration /= 1000

        return TestResult(
            framework="playwright",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


class TestResultParserService:
    """Service that orchestrates multiple test result parsers."""

    def __init__(self, parsers: list[TestResultParser] | None = None) -> None:
        """Initialize with parsers, using defaults if none provided."""
        self._parsers = parsers or self._get_default_parsers()

    @staticmethod
    def _get_default_parsers() -> list[TestResultParser]:
        """Get default list of parsers."""
        return [
            PytestParser(),
            UnittestParser(),
            Nose2Parser(),
            JestParser(),
            GoTestParser(),
            MochaParser(),
            VitestParser(),
            PlaywrightParser(),
            RSpecParser(),
            MinitestParser(),
            CargoTestParser(),
            PHPUnitParser(),
            JUnitParser(),
            TestNGParser(),
            DotNetParser(),
        ]

    def parse(self, log_content: str) -> TestResult | None:
        """Try all parsers until one succeeds."""
        if not log_content:
            return None

        for parser in self._parsers:
            if parser.can_parse(log_content):
                result = parser.parse(log_content)
                if result is not None:
                    return result
        return None
