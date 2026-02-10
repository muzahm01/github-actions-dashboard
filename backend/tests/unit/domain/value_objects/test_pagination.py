"""Tests for Pagination value objects."""

import pytest

from app.domain.value_objects.pagination import PaginatedResult, Pagination


class TestPagination:
    """Tests for the Pagination value object."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        p = Pagination()
        assert p.page == 1
        assert p.per_page == 20
        assert p.max_per_page == 100

    @pytest.mark.unit
    def test_custom_values(self) -> None:
        p = Pagination(page=3, per_page=50)
        assert p.page == 3
        assert p.per_page == 50

    @pytest.mark.unit
    def test_page_clamped_to_minimum_1(self) -> None:
        p = Pagination(page=-5)
        assert p.page == 1

    @pytest.mark.unit
    def test_page_zero_clamped(self) -> None:
        p = Pagination(page=0)
        assert p.page == 1

    @pytest.mark.unit
    def test_per_page_clamped_to_minimum_1(self) -> None:
        p = Pagination(per_page=0)
        assert p.per_page == 1

    @pytest.mark.unit
    def test_per_page_negative_clamped(self) -> None:
        p = Pagination(per_page=-10)
        assert p.per_page == 1

    @pytest.mark.unit
    def test_per_page_clamped_to_max(self) -> None:
        p = Pagination(per_page=200, max_per_page=100)
        assert p.per_page == 100

    @pytest.mark.unit
    def test_custom_max_per_page(self) -> None:
        p = Pagination(per_page=60, max_per_page=50)
        assert p.per_page == 50

    @pytest.mark.unit
    def test_offset_first_page(self) -> None:
        p = Pagination(page=1, per_page=20)
        assert p.offset == 0

    @pytest.mark.unit
    def test_offset_later_page(self) -> None:
        p = Pagination(page=3, per_page=10)
        assert p.offset == 20

    @pytest.mark.unit
    def test_limit_equals_per_page(self) -> None:
        p = Pagination(per_page=25)
        assert p.limit == 25

    @pytest.mark.unit
    def test_first_page_factory(self) -> None:
        p = Pagination.first_page(per_page=15)
        assert p.page == 1
        assert p.per_page == 15

    @pytest.mark.unit
    def test_next_page(self) -> None:
        p = Pagination(page=2, per_page=10)
        n = p.next_page()
        assert n.page == 3
        assert n.per_page == 10

    @pytest.mark.unit
    def test_prev_page(self) -> None:
        p = Pagination(page=3, per_page=10)
        prev = p.prev_page()
        assert prev.page == 2
        assert prev.per_page == 10

    @pytest.mark.unit
    def test_prev_page_at_first_returns_self(self) -> None:
        p = Pagination(page=1, per_page=10)
        prev = p.prev_page()
        assert prev.page == 1

    @pytest.mark.unit
    def test_frozen(self) -> None:
        p = Pagination()
        with pytest.raises(AttributeError):
            p.page = 5  # type: ignore[misc]


class TestPaginatedResult:
    """Tests for the PaginatedResult value object."""

    @pytest.mark.unit
    def test_total_pages(self) -> None:
        r = PaginatedResult(items=[1, 2, 3], total=25, page=1, per_page=10)
        assert r.total_pages == 3

    @pytest.mark.unit
    def test_total_pages_exact(self) -> None:
        r = PaginatedResult(items=[1, 2], total=20, page=1, per_page=10)
        assert r.total_pages == 2

    @pytest.mark.unit
    def test_total_pages_zero_per_page(self) -> None:
        r = PaginatedResult(items=[], total=10, page=1, per_page=0)
        assert r.total_pages == 0

    @pytest.mark.unit
    def test_has_next(self) -> None:
        r = PaginatedResult(items=[1], total=25, page=1, per_page=10)
        assert r.has_next is True

    @pytest.mark.unit
    def test_has_next_last_page(self) -> None:
        r = PaginatedResult(items=[1], total=25, page=3, per_page=10)
        assert r.has_next is False

    @pytest.mark.unit
    def test_has_prev(self) -> None:
        r = PaginatedResult(items=[1], total=25, page=2, per_page=10)
        assert r.has_prev is True

    @pytest.mark.unit
    def test_has_prev_first_page(self) -> None:
        r = PaginatedResult(items=[1], total=25, page=1, per_page=10)
        assert r.has_prev is False

    @pytest.mark.unit
    def test_is_empty(self) -> None:
        r = PaginatedResult(items=[], total=0, page=1, per_page=10)
        assert r.is_empty is True

    @pytest.mark.unit
    def test_is_not_empty(self) -> None:
        r = PaginatedResult(items=["a"], total=1, page=1, per_page=10)
        assert r.is_empty is False

    @pytest.mark.unit
    def test_empty_factory(self) -> None:
        r = PaginatedResult.empty(page=1, per_page=10)
        assert r.items == []
        assert r.total == 0
        assert r.is_empty is True
        assert r.has_next is False
        assert r.has_prev is False
