# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Cache-aside pattern with Redis TTL for dashboard stats endpoint
- REDIS_URL documentation in `.env.example`
- CONTRIBUTING.md and CHANGELOG.md project documentation
- Full type annotations for all Celery task files
- Application service layer for all API routers (clean architecture compliance)
- Database indexes on `workflow_runs.status` and `jobs.conclusion` columns
- Pagination (`limit`/`offset`) on unbounded repository queries
- `selectinload` eager loading to prevent N+1 queries

### Changed
- Decomposed `test_result_parser.py` (932 lines) into per-framework parser modules under `parsers/` sub-package
- Reduced cyclomatic complexity of `update_prompt()` and `process_workflow_run()`
- Upgraded `redis` from 5.2.1 to 7.1.1
- Upgraded `python-json-logger` from 2.0.7 to 4.0.0
- Replaced `datetime.utcnow()` with `datetime.now(UTC)` across codebase
- Replaced bare `dict` returns with Pydantic response models in API endpoints
- Switched webhook signature verification from `==` to `hmac.compare_digest`

### Fixed
- Missing `await` on async repository calls in API routers
- Integer overflow risk in `data_retention_days` setting (added `le=3650` bound)
- Potential timing attack in webhook HMAC comparison
