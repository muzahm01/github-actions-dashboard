"""Per-framework test result parsers."""

from app.application.services.parsers.base import (
    BaseParser,
    FailureDetail,
    TestResult,
    TestResultParser,
)
from app.application.services.parsers.javascript import (
    JestParser,
    MochaParser,
    PlaywrightParser,
    VitestParser,
)
from app.application.services.parsers.jvm import JUnitParser, TestNGParser
from app.application.services.parsers.python import (
    Nose2Parser,
    PytestParser,
    UnittestParser,
)
from app.application.services.parsers.ruby import MinitestParser, RSpecParser
from app.application.services.parsers.systems import (
    CargoTestParser,
    DotNetParser,
    GoTestParser,
    PHPUnitParser,
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
    "UnittestParser",
    "VitestParser",
]
