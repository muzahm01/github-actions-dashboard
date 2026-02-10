"""Tests for SearchQuery and SearchResult value objects."""

import pytest

from app.domain.value_objects.search_query import SearchQuery, SearchResult, SearchType


class TestSearchQuery:
    """Tests for the SearchQuery value object."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        q = SearchQuery(query="test error")
        assert q.query == "test error"
        assert q.search_type == SearchType.SEMANTIC
        assert q.limit == 20
        assert q.min_score == 0.5

    @pytest.mark.unit
    def test_limit_clamped_low(self) -> None:
        q = SearchQuery(query="x", limit=0)
        assert q.limit == 1

    @pytest.mark.unit
    def test_limit_clamped_high(self) -> None:
        q = SearchQuery(query="x", limit=200)
        assert q.limit == 100

    @pytest.mark.unit
    def test_min_score_clamped_low(self) -> None:
        q = SearchQuery(query="x", min_score=-0.5)
        assert q.min_score == 0.0

    @pytest.mark.unit
    def test_min_score_clamped_high(self) -> None:
        q = SearchQuery(query="x", min_score=1.5)
        assert q.min_score == 1.0

    @pytest.mark.unit
    def test_semantic_factory(self) -> None:
        q = SearchQuery.semantic("find errors", limit=10)
        assert q.search_type == SearchType.SEMANTIC
        assert q.limit == 10

    @pytest.mark.unit
    def test_text_factory(self) -> None:
        q = SearchQuery.text("find errors", limit=5)
        assert q.search_type == SearchType.TEXT
        assert q.limit == 5

    @pytest.mark.unit
    def test_hybrid_factory(self) -> None:
        q = SearchQuery.hybrid("find errors")
        assert q.search_type == SearchType.HYBRID

    @pytest.mark.unit
    def test_with_repository_filter(self) -> None:
        q = SearchQuery.semantic("test")
        filtered = q.with_repository_filter(1, 2, 3)
        assert filtered.repository_ids == (1, 2, 3)
        assert filtered.query == "test"
        assert filtered.search_type == SearchType.SEMANTIC

    @pytest.mark.unit
    def test_with_repository_filter_preserves_other_fields(self) -> None:
        q = SearchQuery(query="x", min_score=0.8, limit=50)
        filtered = q.with_repository_filter(10)
        assert filtered.min_score == 0.8
        assert filtered.limit == 50

    @pytest.mark.unit
    def test_frozen(self) -> None:
        q = SearchQuery(query="test")
        with pytest.raises(AttributeError):
            q.query = "other"  # type: ignore[misc]


class TestSearchResult:
    """Tests for the SearchResult value object."""

    @pytest.mark.unit
    def test_from_log(self) -> None:
        r = SearchResult.from_log(
            log_id=42,
            job_name="build-test",
            content_preview="Error: test failed at line 10",
            score=0.85,
        )
        assert r.id == 42
        assert r.result_type == "log"
        assert r.title == "Log: build-test"
        assert r.score == 0.85

    @pytest.mark.unit
    def test_from_log_truncates_description(self) -> None:
        long_content = "x" * 300
        r = SearchResult.from_log(
            log_id=1,
            job_name="test",
            content_preview=long_content,
        )
        assert len(r.description) == 200

    @pytest.mark.unit
    def test_from_workflow(self) -> None:
        r = SearchResult.from_workflow(
            workflow_id=7,
            name="CI Pipeline",
            path=".github/workflows/ci.yml",
            score=0.9,
        )
        assert r.id == 7
        assert r.result_type == "workflow"
        assert r.title == "CI Pipeline"
        assert r.description == ".github/workflows/ci.yml"

    @pytest.mark.unit
    def test_is_relevant_above_threshold(self) -> None:
        r = SearchResult(id=1, result_type="log", title="t", score=0.8)
        assert r.is_relevant(threshold=0.5) is True

    @pytest.mark.unit
    def test_is_relevant_below_threshold(self) -> None:
        r = SearchResult(id=1, result_type="log", title="t", score=0.3)
        assert r.is_relevant(threshold=0.5) is False

    @pytest.mark.unit
    def test_is_relevant_at_threshold(self) -> None:
        r = SearchResult(id=1, result_type="log", title="t", score=0.5)
        assert r.is_relevant(threshold=0.5) is True

    @pytest.mark.unit
    def test_is_relevant_default_threshold(self) -> None:
        r = SearchResult(id=1, result_type="log", title="t", score=0.6)
        assert r.is_relevant() is True

    @pytest.mark.unit
    def test_from_log_with_metadata(self) -> None:
        r = SearchResult.from_log(
            log_id=1,
            job_name="test",
            content_preview="error",
            score=0.7,
            run_id=123,
        )
        assert r.metadata["run_id"] == 123
