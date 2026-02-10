"""JavaScript/TypeScript test framework parsers (Jest, Mocha, Vitest, Playwright)."""

from __future__ import annotations

import re

from app.application.services.parsers.base import BaseParser, TestResult


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
