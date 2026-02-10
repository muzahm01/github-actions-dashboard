"""Python test framework parsers (pytest, unittest, nose2)."""

from __future__ import annotations

import re

from app.application.services.parsers.base import BaseParser, FailureDetail, TestResult


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
