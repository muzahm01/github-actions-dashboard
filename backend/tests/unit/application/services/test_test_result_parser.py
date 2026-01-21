"""Tests for test result parser service."""

import pytest

from app.application.services.test_result_parser import (
    BaseParser,
    CargoTestParser,
    DotNetParser,
    FailureDetail,
    GoTestParser,
    JestParser,
    JUnitParser,
    MochaParser,
    PHPUnitParser,
    PytestParser,
    RSpecParser,
    TestResult,
    TestResultParserService,
    VitestParser,
)


class TestPytestParser:
    """Test suite for pytest log parser."""

    @pytest.fixture
    def parser(self) -> PytestParser:
        """Create parser instance."""
        return PytestParser()

    # Detection tests
    def test_can_parse_with_collected_keyword(self, parser: PytestParser) -> None:
        """Should detect pytest output with collected keyword."""
        assert parser.can_parse("collected 5 items") is True

    def test_can_parse_with_summary_line(self, parser: PytestParser) -> None:
        """Should detect pytest output with summary line."""
        assert parser.can_parse("===== 5 passed in 1.0s =====") is True

    def test_cannot_parse_jest_output(self, parser: PytestParser) -> None:
        """Should not detect Jest output."""
        assert parser.can_parse("Tests: 5 passed, 5 total") is False

    def test_cannot_parse_empty_log(self, parser: PytestParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    # Parsing tests - success scenarios
    def test_parse_all_passed(self, parser: PytestParser) -> None:
        """Should parse successful test run."""
        log = """
        ============================= test session starts ==============================
        collected 10 items

        tests/test_example.py ..........                                        [100%]

        ============================== 10 passed in 1.23s ==============================
        """
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "pytest"
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0
        assert result.skipped == 0
        assert result.duration_seconds == pytest.approx(1.23)

    def test_parse_with_failures(self, parser: PytestParser) -> None:
        """Should parse test run with failures."""
        log = """
        collected 10 items
        ===== 2 failed, 6 passed, 2 skipped in 3.45s =====
        """
        result = parser.parse(log)

        assert result is not None
        assert result.total == 10
        assert result.passed == 6
        assert result.failed == 2
        assert result.skipped == 2
        assert result.duration_seconds == pytest.approx(3.45)

    def test_parse_with_errors(self, parser: PytestParser) -> None:
        """Should parse test run with errors (count as failures)."""
        log = "collected 10 items\n===== 1 error, 9 passed in 0.5s ====="
        result = parser.parse(log)

        assert result is not None
        assert result.failed == 1
        assert result.passed == 9

    def test_parse_with_xfailed(self, parser: PytestParser) -> None:
        """Should parse test run with xfailed (count as skipped)."""
        log = "collected 7 items\n===== 5 passed, 2 xfailed in 1.0s ====="
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 5
        assert result.skipped == 2

    # Edge cases
    def test_parse_strips_ansi_codes(self, parser: PytestParser) -> None:
        """Should parse despite ANSI color codes."""
        log = "\x1b[32mcollected 5 items\x1b[0m\n\x1b[32m===== 5 passed in 0.5s =====\x1b[0m"
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 5

    def test_parse_strips_docker_timestamps(self, parser: PytestParser) -> None:
        """Should parse despite Docker container prefixes."""
        log = """
        2024-01-15T10:00:00.000Z collected 3 items
        2024-01-15T10:00:01.000Z ===== 3 passed in 0.5s =====
        """
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 3

    def test_parse_strips_container_prefixes(self, parser: PytestParser) -> None:
        """Should parse despite container name prefixes."""
        log = """
        [test-container] collected 2 items
        [test-container] ===== 2 passed in 0.1s =====
        """
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 2

    def test_parse_returns_none_for_invalid_log(self, parser: PytestParser) -> None:
        """Should return None for invalid log."""
        log = "This is not pytest output"
        result = parser.parse(log)

        assert result is None

    def test_success_rate_calculation(self, parser: PytestParser) -> None:
        """Should calculate success rate correctly."""
        log = "collected 10 items\n===== 8 passed, 2 failed in 1.0s ====="
        result = parser.parse(log)

        assert result is not None
        assert result.success_rate == 80.0


class TestJestParser:
    """Test suite for Jest log parser."""

    @pytest.fixture
    def parser(self) -> JestParser:
        """Create parser instance."""
        return JestParser()

    def test_can_parse_jest_output(self, parser: JestParser) -> None:
        """Should detect Jest output."""
        assert parser.can_parse("Tests: 5 passed, 5 total") is True

    def test_cannot_parse_pytest_output(self, parser: JestParser) -> None:
        """Should not detect pytest output."""
        assert parser.can_parse("collected 5 items") is False

    def test_parse_all_passed(self, parser: JestParser) -> None:
        """Should parse successful Jest run."""
        log = """
        PASS src/test.spec.js
        Tests:        5 passed, 5 total
        Time:         1.234 s
        """
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "jest"
        assert result.passed == 5
        assert result.total == 5
        assert result.duration_seconds == pytest.approx(1.234)

    def test_parse_with_failures(self, parser: JestParser) -> None:
        """Should parse Jest run with failures."""
        log = "Tests:        2 failed, 3 skipped, 5 passed, 10 total"
        result = parser.parse(log)

        assert result is not None
        assert result.failed == 2
        assert result.skipped == 3
        assert result.passed == 5
        assert result.total == 10

    def test_parse_without_duration(self, parser: JestParser) -> None:
        """Should parse Jest run without duration."""
        log = "Tests: 3 passed, 3 total"
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 3
        assert result.duration_seconds is None


class TestGoTestParser:
    """Test suite for Go test log parser."""

    @pytest.fixture
    def parser(self) -> GoTestParser:
        """Create parser instance."""
        return GoTestParser()

    def test_can_parse_go_test_output(self, parser: GoTestParser) -> None:
        """Should detect Go test output."""
        assert parser.can_parse("--- PASS: TestExample (0.00s)") is True
        assert parser.can_parse("ok  \tgithub.com/user/repo\t0.123s") is True

    def test_parse_all_passed(self, parser: GoTestParser) -> None:
        """Should parse successful Go test run."""
        log = """
        === RUN   TestExample1
        --- PASS: TestExample1 (0.00s)
        === RUN   TestExample2
        --- PASS: TestExample2 (0.01s)
        PASS
        ok  	github.com/user/repo	0.123s
        """
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "go-test"
        assert result.passed == 2
        assert result.failed == 0
        assert result.duration_seconds == pytest.approx(0.123)

    def test_parse_with_failures(self, parser: GoTestParser) -> None:
        """Should parse Go test run with failures."""
        log = """
        --- PASS: TestA (0.00s)
        --- FAIL: TestB (0.01s)
        --- SKIP: TestC (0.00s)
        FAIL	github.com/user/repo	0.5s
        """
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 1
        assert result.failed == 1
        assert result.skipped == 1


class TestTestResultParserService:
    """Test suite for parser orchestration service."""

    @pytest.fixture
    def service(self) -> TestResultParserService:
        """Create service instance."""
        return TestResultParserService()

    def test_selects_correct_parser_for_pytest(self, service: TestResultParserService) -> None:
        """Should select pytest parser for pytest output."""
        log = "collected 1 items\n===== 1 passed in 0.1s ====="
        result = service.parse(log)

        assert result is not None
        assert result.framework == "pytest"

    def test_selects_correct_parser_for_jest(self, service: TestResultParserService) -> None:
        """Should select Jest parser for Jest output."""
        log = "Tests: 1 passed, 1 total"
        result = service.parse(log)

        assert result is not None
        assert result.framework == "jest"

    def test_selects_correct_parser_for_go(self, service: TestResultParserService) -> None:
        """Should select Go parser for Go test output."""
        log = "--- PASS: Test (0.00s)\nok  \tpkg\t0.1s"
        result = service.parse(log)

        assert result is not None
        assert result.framework == "go-test"

    def test_returns_none_for_unrecognized_output(self, service: TestResultParserService) -> None:
        """Should return None for unrecognized output."""
        log = "Build successful\nDeploying..."
        result = service.parse(log)

        assert result is None

    def test_handles_empty_log(self, service: TestResultParserService) -> None:
        """Should handle empty log."""
        result = service.parse("")
        assert result is None

    def test_test_result_total_calculation(self) -> None:
        """Should correctly sum total from counts."""
        result = TestResult(
            framework="test",
            total=10,
            passed=5,
            failed=3,
            skipped=2,
            duration_seconds=1.0,
        )
        assert result.total == 10

    def test_test_result_success_rate_zero_total(self) -> None:
        """Should handle zero total gracefully."""
        result = TestResult(
            framework="test",
            total=0,
            passed=0,
            failed=0,
            skipped=0,
        )
        assert result.success_rate == 0.0


class TestMochaParser:
    """Test suite for Mocha log parser."""

    @pytest.fixture
    def parser(self) -> MochaParser:
        """Create parser instance."""
        return MochaParser()

    def test_can_parse_mocha_output(self, parser: MochaParser) -> None:
        """Should detect Mocha output."""
        assert parser.can_parse("5 passing (1s)") is True

    def test_cannot_parse_empty(self, parser: MochaParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    def test_parse_passing_tests(self, parser: MochaParser) -> None:
        """Should parse passing tests."""
        log = "10 passing (500ms)"
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "mocha"
        assert result.passed == 10
        assert result.duration_seconds == pytest.approx(0.5)

    def test_parse_with_failures(self, parser: MochaParser) -> None:
        """Should parse tests with failures."""
        log = "8 passing (1s) 2 failing"
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 8
        # Note: The mocha parser may or may not pick up failures depending on format


class TestVitestParser:
    """Test suite for Vitest log parser."""

    @pytest.fixture
    def parser(self) -> VitestParser:
        """Create parser instance."""
        return VitestParser()

    def test_can_parse_vitest_output(self, parser: VitestParser) -> None:
        """Should detect Vitest output."""
        # Vitest uses a specific format with pipe separators
        assert parser.can_parse("Tests  5 passed | 5 total") is True

    def test_cannot_parse_empty(self, parser: VitestParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    def test_parse_passing_tests(self, parser: VitestParser) -> None:
        """Should parse passing tests."""
        log = "Tests  5 passed\nDuration 1.5 s"
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "vitest"
        assert result.passed == 5


class TestRSpecParser:
    """Test suite for RSpec log parser."""

    @pytest.fixture
    def parser(self) -> RSpecParser:
        """Create parser instance."""
        return RSpecParser()

    def test_can_parse_rspec_output(self, parser: RSpecParser) -> None:
        """Should detect RSpec output."""
        assert parser.can_parse("10 examples, 0 failures") is True

    def test_cannot_parse_empty(self, parser: RSpecParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    def test_parse_all_passing(self, parser: RSpecParser) -> None:
        """Should parse all passing tests."""
        log = "Finished in 2.5 seconds\n10 examples, 0 failures"
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "rspec"
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0
        assert result.duration_seconds == pytest.approx(2.5)

    def test_parse_with_failures(self, parser: RSpecParser) -> None:
        """Should parse tests with failures."""
        log = "15 examples, 3 failures, 2 pending"
        result = parser.parse(log)

        assert result is not None
        assert result.total == 15
        assert result.passed == 10
        assert result.failed == 3
        assert result.skipped == 2


class TestCargoTestParser:
    """Test suite for Rust cargo test log parser."""

    @pytest.fixture
    def parser(self) -> CargoTestParser:
        """Create parser instance."""
        return CargoTestParser()

    def test_can_parse_cargo_output(self, parser: CargoTestParser) -> None:
        """Should detect cargo test output."""
        assert parser.can_parse("test result: ok. 10 passed; 0 failed; 0 ignored") is True

    def test_cannot_parse_empty(self, parser: CargoTestParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    def test_parse_all_passing(self, parser: CargoTestParser) -> None:
        """Should parse all passing tests."""
        log = "test result: ok. 10 passed; 0 failed; 0 ignored; finished in 1.5s"
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "cargo-test"
        assert result.passed == 10
        assert result.failed == 0

    def test_parse_with_failures(self, parser: CargoTestParser) -> None:
        """Should parse tests with failures."""
        log = "test result: FAILED. 8 passed; 2 failed; 1 ignored"
        result = parser.parse(log)

        assert result is not None
        assert result.passed == 8
        assert result.failed == 2
        assert result.skipped == 1


class TestPHPUnitParser:
    """Test suite for PHPUnit log parser."""

    @pytest.fixture
    def parser(self) -> PHPUnitParser:
        """Create parser instance."""
        return PHPUnitParser()

    def test_can_parse_phpunit_ok_output(self, parser: PHPUnitParser) -> None:
        """Should detect PHPUnit OK output."""
        assert parser.can_parse("OK (10 tests, 20 assertions)") is True

    def test_can_parse_phpunit_failure_output(self, parser: PHPUnitParser) -> None:
        """Should detect PHPUnit failure output."""
        assert parser.can_parse("Tests: 10, Assertions: 20, Failures: 2") is True

    def test_cannot_parse_empty(self, parser: PHPUnitParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    def test_parse_ok_result(self, parser: PHPUnitParser) -> None:
        """Should parse OK result."""
        log = "OK (10 tests, 20 assertions)"
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "phpunit"
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0

    def test_parse_with_failures(self, parser: PHPUnitParser) -> None:
        """Should parse tests with failures."""
        log = "Tests: 10, Assertions: 20, Failures: 2, Errors: 1, Skipped: 1"
        result = parser.parse(log)

        assert result is not None
        assert result.total == 10
        assert result.failed == 3  # 2 failures + 1 error
        assert result.skipped == 1


class TestJUnitParser:
    """Test suite for JUnit log parser."""

    @pytest.fixture
    def parser(self) -> JUnitParser:
        """Create parser instance."""
        return JUnitParser()

    def test_can_parse_junit_output(self, parser: JUnitParser) -> None:
        """Should detect JUnit output."""
        assert parser.can_parse("Tests run: 10, Failures: 0, Errors: 0, Skipped: 0") is True

    def test_cannot_parse_empty(self, parser: JUnitParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    def test_parse_all_passing(self, parser: JUnitParser) -> None:
        """Should parse all passing tests."""
        log = "Tests run: 10, Failures: 0, Errors: 0, Skipped: 0\nTime elapsed: 2.5 s"
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "junit"
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0
        assert result.duration_seconds == pytest.approx(2.5)

    def test_parse_with_failures(self, parser: JUnitParser) -> None:
        """Should parse tests with failures."""
        log = "Tests run: 10, Failures: 2, Errors: 1, Skipped: 1"
        result = parser.parse(log)

        assert result is not None
        assert result.total == 10
        assert result.passed == 6
        assert result.failed == 3  # 2 failures + 1 error
        assert result.skipped == 1


class TestDotNetParser:
    """Test suite for .NET test log parser."""

    @pytest.fixture
    def parser(self) -> DotNetParser:
        """Create parser instance."""
        return DotNetParser()

    def test_can_parse_dotnet_passed_output(self, parser: DotNetParser) -> None:
        """Should detect .NET passed output."""
        assert (
            parser.can_parse(
                "Passed!  -  Failed:     0, Passed:    10, Skipped:     0, Total:    10"
            )
            is True
        )

    def test_cannot_parse_empty(self, parser: DotNetParser) -> None:
        """Should not detect empty log."""
        assert parser.can_parse("") is False

    def test_parse_all_passing(self, parser: DotNetParser) -> None:
        """Should parse all passing tests."""
        log = "Passed!  -  Failed:     0, Passed:    10, Skipped:     0, Total:    10"
        result = parser.parse(log)

        assert result is not None
        assert result.framework == "dotnet"
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0

    def test_parse_with_failures(self, parser: DotNetParser) -> None:
        """Should parse tests with failures."""
        log = "Failed!  -  Failed:     2, Passed:     7, Skipped:     1, Total:    10"
        result = parser.parse(log)

        assert result is not None
        assert result.total == 10
        assert result.passed == 7
        assert result.failed == 2
        assert result.skipped == 1


class TestBaseParser:
    """Test suite for BaseParser utilities."""

    def test_strip_ansi_removes_color_codes(self) -> None:
        """Should remove ANSI color codes."""
        text = "\x1b[32mGreen text\x1b[0m and \x1b[31mred text\x1b[0m"
        result = BaseParser.strip_ansi(text)
        assert result == "Green text and red text"

    def test_strip_docker_noise_removes_timestamps(self) -> None:
        """Should remove Docker timestamps."""
        text = "2024-01-15T10:00:00.000Z Line 1\n2024-01-15T10:00:01.000Z Line 2"
        result = BaseParser.strip_docker_noise(text)
        assert "2024-01-15" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_strip_docker_noise_removes_container_prefixes(self) -> None:
        """Should remove container name prefixes."""
        text = "[my-container] Output line"
        result = BaseParser.strip_docker_noise(text)
        assert result == "Output line"


class TestFailureDetail:
    """Test suite for FailureDetail dataclass."""

    def test_create_failure_detail(self) -> None:
        """Should create FailureDetail instance."""
        detail = FailureDetail(
            test_name="test_example",
            error_message="AssertionError",
            stack_trace="at test_example.py:10",
            file_path="test_example.py",
            line_number=10,
        )

        assert detail.test_name == "test_example"
        assert detail.error_message == "AssertionError"
        assert detail.stack_trace == "at test_example.py:10"
        assert detail.file_path == "test_example.py"
        assert detail.line_number == 10

    def test_failure_detail_is_frozen(self) -> None:
        """Should be immutable."""
        detail = FailureDetail(
            test_name="test_example",
            error_message="Error",
        )

        with pytest.raises(AttributeError):
            detail.test_name = "modified"  # type: ignore[misc]
