"""Multi-framework test result parser.

This module re-exports all parser classes from the parsers sub-package
for backward compatibility, and contains the TestResultParserService
orchestrator.
"""

from __future__ import annotations

from app.application.services.parsers import (
    BaseParser,
    CargoTestParser,
    DotNetParser,
    FailureDetail,
    GoTestParser,
    JestParser,
    JUnitParser,
    MinitestParser,
    MochaParser,
    Nose2Parser,
    PHPUnitParser,
    PlaywrightParser,
    PytestParser,
    RSpecParser,
    TestNGParser,
    TestResult,
    TestResultParser,
    UnittestParser,
    VitestParser,
)

__all__ = [
    "BaseParser",
    "CargoTestParser",
    "DotNetParser",
    "FailureDetail",
    "GoTestParser",
    "JUnitParser",
    "JestParser",
    "MinitestParser",
    "MochaParser",
    "Nose2Parser",
    "PHPUnitParser",
    "PlaywrightParser",
    "PytestParser",
    "RSpecParser",
    "TestNGParser",
    "TestResult",
    "TestResultParser",
    "TestResultParserService",
    "UnittestParser",
    "VitestParser",
]


class TestResultParserService:
    """Service that orchestrates multiple test result parsers."""

    __test__ = False  # Prevent pytest collection

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
