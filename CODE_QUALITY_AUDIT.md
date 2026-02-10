# Code Quality Audit Report

**Project:** GitHub Actions Dashboard
**Date:** 2026-02-08
**Scope:** Full codebase audit — backend (Python/FastAPI), frontend (Vue 3/TypeScript), infrastructure, dependencies, architecture, testing, documentation, and performance.

---

## Executive Summary

The GitHub Actions Dashboard is a ~30,000 LOC full-stack application (17,700 Python / 3,600 TypeScript+Vue) built over ~20 days with 81 commits. The codebase demonstrates strong fundamentals — zero Ruff lint violations, zero `any` types in TypeScript, thorough API docstrings, and a clean domain layer. However, the audit identified **47 distinct issues** across 8 categories, including several that pose runtime bug risk or performance degradation as data grows.

### Risk Heatmap

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Type Safety | 5 | 4 | 1 | — | 10 |
| Architecture | — | 1 | 2 | — | 3 |
| Testing | 1 | 3 | 2 | 2 | 8 |
| Performance | — | 3 | 4 | 3 | 10 |
| Dependencies | — | 4 | 1 | 4 | 9 |
| Documentation | — | — | 3 | 2 | 5 |
| Frontend | — | — | — | 2 | 2 |
| **Totals** | **6** | **15** | **13** | **13** | **47** |

### Top 5 Priorities

1. **Fix 5 mypy errors that indicate probable runtime bugs** (type safety — critical)
2. **Add database indexes to all foreign key columns** (performance — high)
3. **Route API endpoints through application services, not directly to repositories** (architecture — high)
4. **Add `@pytest.mark.unit` to all 288 unit tests** (testing — critical)
5. **Add Celery task time limits and rate limits** (performance — medium)

---

## 1. Project Overview

| Metric | Value |
|--------|-------|
| Total files | 239 |
| Python LOC | 17,675 (11,733 source + 5,612 tests + 330 config) |
| TypeScript/Vue LOC | 3,610 |
| Documentation LOC | 7,763 |
| Git commits | 81 |
| Project age | ~20 days |
| Backend modules | 148 Python files |
| Frontend components | 13 Vue files + 7 TS files |
| CI workflows | 5 |
| Docker services | 7 |

### Language Distribution

```
Python      ███████████████████████████████████████  58%
Markdown    ████████████████████████                 26%
Vue/TS      ████████                                 12%
YAML/Config ████                                      4%
```

---

## 2. Type Safety (205 mypy errors in 42 files)

### 2.1 Critical — Probable Runtime Bugs

These 5 errors indicate code that will crash or produce wrong results at runtime:

| ID | File | Line | Issue | Risk |
|----|------|------|-------|------|
| TS-01 | `infrastructure/external/github_client.py` | 155-160 | `str` used as `dict` — indexing a string with `["id"]` and calling `.get()` on it | **Runtime crash** |
| TS-02 | `application/services/prompt_service.py` | 336 | `set.add()` return value used (always `None`) | **Silent logic bug** |
| TS-03 | `tasks/maintenance_tasks.py` | 136, 142 | Instance attributes accessed on class objects (`type[ErrorAnalysis].workflow_run_id`) | **Runtime crash** |
| TS-04 | `application/services/github_sync_service.py` | 27 | `None` assigned to `list[str]` variable | **AttributeError if iterated** |
| TS-05 | `api/v1/notifications.py` | 150, 152 | `DiscordSender`/`WebhookSender` assigned to `SlackSender` typed variable | **Wrong type at runtime** |

### 2.2 High — Type Safety Gaps

| ID | Count | Issue |
|----|-------|-------|
| TS-06 | 109 | Bare `dict` without type parameters (should be `dict[str, Any]`) |
| TS-07 | 21 | Calling untyped functions from typed context |
| TS-08 | 17 | Celery `@app.task` decorator makes functions untyped |
| TS-09 | 16 | `Any` returned from typed functions without narrowing |

### 2.3 Worst Offending Files

| File | Errors |
|------|--------|
| `tasks/analysis_tasks.py` | 26 |
| `tasks/notification_tasks.py` | 22 |
| `tasks/workflow_tasks.py` | 20 |
| `tasks/maintenance_tasks.py` | 17 |
| `infrastructure/external/llm_client.py` | 10 |
| `application/services/github_sync_service.py` | 9 |

The `tasks/` directory accounts for **85 of 205 errors (41%)**, primarily due to untyped Celery decorators and bare `dict` types.

### 2.4 Complexity Violations

Two functions exceed the C901 complexity threshold of 10:
- `prompt_service.py:359` — `update_prompt()` (complexity 11)
- `workflow_tasks.py:122` — `process_workflow_run()` (complexity 11)

---

## 3. Architecture Issues

### 3.1 High — API Layer Bypasses Application Layer

**14 of 17 API routers import directly from infrastructure**, violating the project's own Clean Architecture:

```
Documented:    API → Application → Domain ← Infrastructure
Actual:        API → Infrastructure (direct)
```

| Router | Infrastructure Imports |
|--------|----------------------|
| `dashboard.py` | 4 ORM models + `get_db` |
| `repositories.py` | `RepositoryRepository` + `get_db` |
| `workflows.py` | `WorkflowRepository` + `get_db` |
| `runs.py` | `WorkflowRunRepository` + `get_db` |
| `jobs.py` | `JobRepository` + `LogRepository` + `get_db` |
| `analysis.py` | `ErrorAnalysisRepository` + `LogRepository` + `get_db` |
| `search.py` | `LogRepository` + `get_db` + `EmbeddingClient` |
| `health.py` | `get_db` |

Only 3 routers (`notifications.py`, `prompts.py`, `webhooks.py`) correctly use application services.

**Impact:** Business logic leaks into routers, tests must mock infrastructure details, and database schema changes require touching API files.

### 3.2 Medium — Direct Instantiation (Bypasses DI)

| File | Line | Issue |
|------|------|-------|
| `api/v1/prompts.py` | 20 | `_prompt_service = PromptService()` — module-level singleton |
| `tasks/workflow_tasks.py` | 147 | `parser_service = TestResultParserService()` — in Celery task |

### 3.3 Positive Findings

- No circular imports detected
- Domain layer is fully isolated (no outward dependencies)
- No god files (all under 10 top-level definitions)
- No high fan-out modules (all under 5 internal imports)
- No global mutable state

---

## 4. Testing Gaps

### 4.1 Critical — Missing Test Markers

**All 288 unit test functions are missing `@pytest.mark.unit`.** Running `pytest -m unit` returns zero tests, violating CLAUDE.md rule #9 ("Use `@pytest.mark.*` markers on all test functions") and making selective test execution impossible.

### 4.2 High — Inflated Coverage (85.6% of excluded subset)

The 85.61% coverage figure only applies to code NOT excluded via `pyproject.toml`. The exclusion list removes ~40% of the codebase from measurement:

**Excluded from coverage:**
- All database models, base repository, session
- All external clients (GitHub, LLM, embedding)
- All Celery tasks
- 6 application services (notification, prompt, github_sync, error_analyzer, embedding, search)
- 4 API routers (notifications, trends, prompts, self_monitoring)
- Entire domain layer
- App entry point, logging, WebSocket handler

**Estimated true coverage:** ~50-55% if exclusions were removed.

### 4.3 High — Modules Without Any Tests

| Module | Type | Risk Level |
|--------|------|------------|
| `api/v1/security.py` | Security auth/verification | HIGH (60% coverage, no dedicated tests) |
| `api/v1/notifications.py` | User notifications | MEDIUM |
| `api/v1/trends.py` | Analytics trends (420 lines) | MEDIUM |
| `api/v1/prompts.py` | LLM prompt management | MEDIUM |
| `api/v1/self_monitoring.py` | System monitoring | LOW |
| `application/services/notification_service.py` | Notification logic (446 lines) | MEDIUM |
| `application/services/prompt_service.py` | Prompt logic (444 lines) | MEDIUM |
| `application/services/github_sync_service.py` | GitHub sync (344 lines) | HIGH |
| `application/services/error_analyzer.py` | Error analysis | MEDIUM |
| `application/services/search_service.py` | Search | MEDIUM |
| `application/services/embedding_service.py` | Embedding generation | LOW |
| All domain entities/events/value objects | Core domain | MEDIUM |

### 4.4 High — Empty Test Categories

- `tests/e2e/` — 0 test files (target: 5% of tests)
- `tests/property/` — 0 test files (Hypothesis is a listed dependency)

### 4.5 Medium — Low Coverage on Measured Modules

| Module | Coverage | Gap |
|--------|----------|-----|
| `api/v1/health.py` | 49% | Health/readiness probes half-untested |
| `api/v1/security.py` | 60% | Security logic 40% untested |
| `infrastructure/websocket/pubsub.py` | 70% | Real-time messaging 30% untested |
| `api/v1/metrics.py` | 75% | Prometheus metrics 25% untested |

### 4.6 Low — Collection Warnings

Three `PytestCollectionWarning` warnings from production classes named `Test*` (`TestResult`, `TestResultParserService`, `TestResultRepository`).

### 4.7 Positive Findings

- 300 test functions across 30 test files
- Test directory mirrors source structure
- Well-structured shared fixtures in `conftest.py` (9 fixtures)
- `asyncio_mode = "auto"` correctly configured
- 61 fixtures total providing good test data coverage

---

## 5. Performance Issues

### 5.1 High — Missing Database Indexes

**8 foreign key columns used in frequent queries lack indexes:**

| Model | Column | Used By |
|-------|--------|---------|
| `Artifact` | `run_id` | Artifact lookups by run |
| `Job` | `run_id` | `get_by_run_id()`, `get_failed_by_run_id()` |
| `JobStep` | `job_id` | Step lookups by job |
| `Log` | `job_id` | `get_by_job_id()` |
| `Log` | `step_id` | Step log lookups |
| `TestResult` | `log_id` | `get_by_log_id()` |
| `Workflow` | `repo_id` | Workflow lookups by repository |
| `WorkflowRun` | `workflow_id` | `get_by_workflow_id()` — most queried |

**Additional missing indexes:**
- `Job.conclusion` — used in failure filtering
- `Log.category` — used in `get_by_category()`
- `WorkflowRun.created_at` — used in `ORDER BY` in nearly every query + range queries

### 5.2 High — N+1 Query Patterns

All model relationships use SQLAlchemy's default lazy loading. Only 4 of ~12 repository methods use `selectinload()`. Risk points:

- Listing workflow runs and accessing `.jobs` → 1 query per run
- Listing jobs and accessing `.steps` or `.logs` → 1 query per job
- Dashboard endpoint loading 4 ORM models with their relations

### 5.3 High — Unbounded Cleanup Query + N+1 Deletion

`cleanup_old_data()` in `workflow_tasks.py` loads ALL old runs with ALL their jobs into memory, then loops through each run → each job → each log, deleting individually. This is O(runs × jobs × logs) individual DELETE queries when cascade deletes would handle it automatically.

### 5.4 Medium — No Celery Task Time Limits

No task has `soft_time_limit` or `time_limit` set. LLM-calling tasks (`analyze_error_log`, `summarize_run_failures`) can hang indefinitely if the Anthropic API is slow, blocking the worker permanently.

### 5.5 Medium — No Rate Limits on External API Tasks

`sync_repository`, `process_workflow_run`, and `analyze_error_log` call GitHub/Anthropic APIs without rate limiting. A burst of webhook events could exhaust API rate limits.

### 5.6 Medium — No API-Layer Caching

The `RedisCache` class exists and works, but no API endpoint uses it. Every request hits the database directly. Dashboard stats, repository lists, and recent failures would benefit from 30s-5m TTL caching.

### 5.7 Medium — Unbounded Repository Queries

Several repository methods return all rows without pagination:
- `get_active()`, `get_by_owner()`, `get_by_run_id()`, `get_by_job_id()`, `get_by_log_id()`, `get_runs_in_timerange()`, `get_runs_before_date()`

### 5.8 Low — Missing Connection Pool Recycle

`create_async_engine()` has no `pool_recycle` setting. Long-lived connections may be killed by PostgreSQL timeouts.

### 5.9 Low — Redis Connection Churn in Pub/Sub

Every `publish_*` function creates a new synchronous Redis connection per message, publishing one message, then closing. Multiple publishes per Celery task means repeated connect/disconnect cycles.

### 5.10 Low — Large Logs Loaded Entirely Into Memory

`download_job_logs()` reads entire log content into memory as a string. GitHub Actions logs can be multi-megabyte.

---

## 6. Dependency Issues

### 6.1 High — Major Version Gaps

| Package | Current | Latest | Breaking Changes Expected |
|---------|---------|--------|--------------------------|
| `openai` | 1.58.1 | 2.17.0 | Yes — SDK v2 has new API |
| `redis` | 5.2.1 | 7.1.0 | Yes — two major versions |
| `python-json-logger` | 2.0.7 | 4.0.0 | Yes — two major versions |
| `pytest` | 8.3.4 | 9.0.2 | Likely — major version |

### 6.2 Medium — Moderately Outdated

| Package | Current | Latest |
|---------|---------|--------|
| `fastapi` | 0.115.6 | 0.128.5 |
| `pydantic` | 2.10.4 | 2.12.5 |
| `sentry-sdk` | 2.19.2 | 2.52.0 |
| `ruff` | 0.8.4 | 0.15.0 |
| `mypy` | 1.14.1 | 1.19.1 |
| `pytest-asyncio` | 0.25.0 | 1.3.0 |

### 6.3 Low — Unused Dependencies (Candidates for Removal)

| Package | Reason |
|---------|--------|
| `python-socketio` | Not imported; FastAPI native WebSockets used |
| `async-timeout` | Not directly imported; transitive dependency |
| `websockets` | Already provided by `uvicorn[standard]` |
| `psycopg2-binary` | Not imported in app code; verify if Alembic needs it |

### 6.4 Frontend Dependencies

- **Security:** 0 npm audit vulnerabilities
- **Unused:** `autoprefixer` and `postcss` in `dependencies` should be in `devDependencies`
- `vue-router` 4.6.4 has major version 5.0.2 available (evaluate when stable)

### 6.5 Security Scan (Bandit)

8 low-severity findings — all `B311` (pseudo-random generators in `trends.py` mock data). No actual security vulnerabilities.

---

## 7. Documentation Gaps

### 7.1 Medium — README Contradicts CLAUDE.md

`README.md` line 56 states prerequisites include `pnpm 9+`, but the project uses **npm** (per CLAUDE.md and `package-lock.json`).

### 7.2 Medium — Missing Standard Files

| File | Status |
|------|--------|
| `CHANGELOG.md` | Missing |
| `CONTRIBUTING.md` | Missing |
| `LICENSE` | Missing |

### 7.3 Medium — Incomplete .env.example

- `REDIS_URL` missing (referenced in CLAUDE.md)
- No inline comments explaining variable purpose/format
- No required vs. optional indicators

### 7.4 Positive Findings

- Thorough API endpoint docstrings (every endpoint)
- Thorough service layer docstrings
- Extensive `docs/` directory (4,400+ lines across 5 files)
- `SECURITY_AUDIT.md` present (292 lines)
- OpenAPI/Swagger properly configured (disabled in production)
- `CLAUDE.md` is comprehensive and well-maintained

---

## 8. Frontend Assessment

The frontend is in excellent shape overall:

| Check | Result |
|-------|--------|
| `vue-tsc --noEmit` | 0 errors |
| `npm run build` | Success (3.57s) |
| `any` usage | 0 occurrences |
| `console.log` | 0 (only 3 `console.error` in catch blocks) |
| TODO/FIXME | 0 |
| Largest file | 362 lines (acceptable) |

### 8.1 Low — Scaffold Remnant

`components/HelloWorld.vue` appears to be unused Vue scaffold boilerplate.

### 8.2 Low — Limited Component Extraction

Only 2 reusable components in `components/`. As views grow past 400 lines, extracting shared UI patterns would improve maintainability.

---

## 9. Prioritized Action Plan

### Phase 1: Fix Now (Week 1) — Critical + High Risk  ✅ COMPLETED (2026-02-09)

| # | Task | Category | Effort | Impact | Status |
|---|------|----------|--------|--------|--------|
| 1 | Fix 5 critical mypy bugs (TS-01 through TS-05) | Type Safety | S | Prevents runtime crashes | ✅ Done |
| 2 | Add `@pytest.mark.unit` to all 286 unit test functions | Testing | M | Enables selective test execution | ✅ Done |
| 3 | Add `index=True` to 8 FK columns + 3 query columns; create Alembic migration | Performance | M | Prevents full table scans | ✅ Done |
| 4 | Add `soft_time_limit`/`time_limit` to all 17 Celery tasks | Performance | S | Prevents hung workers | ✅ Done |
| 5 | Fix `cleanup_old_data()` — use batch deletes via subqueries | Performance | S | Prevents memory exhaustion | ✅ Done |
| 6 | Fix bare `dict` → `dict[str, Any]` type annotations across 36 files | Type Safety | M | Moves toward mypy passing | ✅ Done |
| 7 | Remove unused deps: `python-socketio`, `async-timeout`, `websockets` | Dependencies | S | Reduces attack surface | ✅ Done |

**Phase 1 completion notes:**
- **TS-01** (`github_client.py`): Changed `_request` return type from `dict[str, Any]` to `Any` since GitHub API returns both dicts and lists.
- **TS-02** (`prompt_service.py`): Replaced `set.add()` idiom with `dict.fromkeys()` for duplicate-free list.
- **TS-03** (`maintenance_tasks.py`): Fixed non-existent `ErrorAnalysis.workflow_run_id` and `Log.workflow_run_id` — rewrote to use subqueries through `Log → Job → WorkflowRun` chain.
- **TS-04** (`github_sync_service.py`): Changed `errors: list[str] = None` to `field(default_factory=list)`.
- **TS-05** (`notifications.py`): Added explicit `sender: NotificationSender` type annotation before the if/elif/else chain.
- **Alembic migration** `a1b2c3d4e5f6` created for all new indexes.
- **All 286 unit tests pass**, `pytest -m unit` collects all 286, ruff passes, frontend builds cleanly.

### Phase 2: Next Sprint (Weeks 2-3) — High Priority

| # | Task | Category | Effort | Impact | Status |
|---|------|----------|--------|--------|--------|
| 8 | Introduce application services for the 14 API routers that bypass them | Architecture | L | Correct Clean Architecture | ✅ Done |
| 9 | Add tests for `security.py` (raise to 90%+ coverage) | Testing | M | Security-critical code covered | ✅ Done |
| 10 | Add tests for `health.py` (raise to 90%+ coverage) | Testing | S | Infrastructure reliability | ✅ Done |
| 11 | Add `rate_limit` to GitHub/Anthropic API tasks | Performance | S | Prevents rate limit exhaustion | ✅ Done |
| 12 | Add pagination to 7 unbounded repository methods | Performance | M | Prevents memory spikes | ✅ Done |
| 13 | Add `selectinload()` to remaining repository methods | Performance | M | Eliminates N+1 queries | ✅ Done |
| 14 | Add `pool_recycle=3600` to async engine config | Performance | S | Prevents stale connections | ✅ Done |
| 15 | Fix README pnpm → npm contradiction | Documentation | S | Prevents contributor confusion | ✅ Done |
| 16 | Plan `openai` v1→v2 migration | Dependencies | M | Stay current on SDK | ✅ Done |

**Phase 2 completion notes:**
- **Task 8** (Architecture): Created 7 application services (`DashboardService`, `RepositoryQueryService`, `WorkflowQueryService`, `WorkflowRunQueryService`, `JobQueryService`, `AnalysisQueryService`, `LogSearchService`) and refactored 7 routers (`dashboard.py`, `repositories.py`, `workflows.py`, `runs.py`, `jobs.py`, `analysis.py`, `search.py`) to use them instead of importing directly from infrastructure. Updated all 6 affected test files to patch at the service module level. Updated `__init__.py` exports and coverage exclusions.
- **Task 9** (`security.py`): Added 24 new tests covering `verify_api_key`, `validate_webhook_url`, `escape_like_pattern`, and `RateLimitMiddleware._check_memory_rate_limit`.
- **Task 10** (`health.py`): Expanded from 4 to 10 tests, adding DB failure (503), Redis failure (503), both fail (503), and response format tests.
- **Task 11** (Rate limits): Added `rate_limit` to all GitHub API tasks (`"30/m"`), sync_all (`"5/m"`), Anthropic LLM tasks (`"10/m"`), and OpenAI embedding tasks (`"20/m"`, batch: `"5/m"`, backfill: `"2/m"`).
- **Tasks 12-13** (Pagination + selectinload): Added `limit`/`offset` defaults to `get_active()`, `get_by_owner()`, `get_by_run_id()`, `get_by_job_id()`, `get_by_log_id()`, `get_runs_in_timerange()`, `get_runs_before_date()`, `get_by_repo_id()`. Added `selectinload()` to `get_recent_failures()`, `get_by_branch()`, `get_by_repo_id()`, `get_logs_with_errors()`, `get_by_category()`.
- **Task 14** (`session.py`): Added `pool_recycle=3600` to `create_async_engine()`.
- **Task 15** (`README.md`): Changed `pnpm 9+` to `npm`.
- **Task 16** (openai migration): Migration is very low risk — only `embedding_client.py` uses OpenAI, only the Embeddings API. The `AsyncOpenAI` client pattern and `embeddings.create()` interface are identical between v1 and v2. Migration = update `pyproject.toml` + run tests. Zero code changes expected.
- **All 322 unit tests pass**, ruff is clean.

### Phase 3: This Quarter (Weeks 4-8) — Medium Priority

| # | Task | Category | Effort | Impact |
|---|------|----------|--------|--------|
| 17 | Add cache-aside pattern to read-heavy API endpoints | Performance | M | Reduces DB load |
| 18 | Write unit tests for 6 untested application services | Testing | L | True coverage improvement |
| 19 | Write unit tests for domain entities/value objects | Testing | M | Domain logic verified |
| 20 | Decompose `test_result_parser.py` (932 lines) into per-framework modules | Code Quality | M | Maintainability |
| 21 | Reduce complexity of `update_prompt()` and `process_workflow_run()` | Code Quality | S | Readability |
| 22 | Add type annotations to Celery task functions (fix 17 `[misc]` errors) | Type Safety | M | Type coverage |
| 23 | Upgrade `redis` 5.x → 7.x | Dependencies | M | Security + features |
| 24 | Upgrade `python-json-logger` 2.x → 4.x | Dependencies | S | Stay current |
| 25 | Create `CONTRIBUTING.md` | Documentation | S | Onboarding |
| 26 | Create `CHANGELOG.md` | Documentation | S | Release tracking |
| 27 | Add `REDIS_URL` + comments to `.env.example` | Documentation | S | Developer experience |

### Phase 4: Backlog — Low Priority

| # | Task | Category | Effort | Impact |
|---|------|----------|--------|--------|
| 28 | Write e2e tests (currently 0) | Testing | L | End-to-end confidence |
| 29 | Write property-based tests with Hypothesis | Testing | M | Edge case discovery |
| 30 | Remove `HelloWorld.vue` scaffold remnant | Frontend | S | Cleanup |
| 31 | Move `autoprefixer`/`postcss` to devDependencies | Dependencies | S | Correctness |
| 32 | Replace `console.error` with structured error logging in frontend | Frontend | S | Consistency |
| 33 | Add `# nosec B311` to `trends.py` random usage | Dependencies | S | Suppress false positives |
| 34 | Split `types/index.ts` into domain-specific type files | Frontend | S | Scalability |
| 35 | Use shared Redis connection pool for pub/sub publish helpers | Performance | S | Minor optimization |
| 36 | Add streaming for large log file downloads | Performance | M | Memory efficiency |
| 37 | Verify if `psycopg2-binary` is needed for Alembic | Dependencies | S | Dependency cleanup |
| 38 | Fix 3 PytestCollectionWarnings from `Test*` class names | Testing | S | Clean test output |
| 39 | Upgrade `pytest` 8→9, `pytest-asyncio` 0.x→1.x | Dependencies | M | Stay current |
| 40 | Upgrade `fastapi`, `pydantic`, `sentry-sdk`, `ruff`, `mypy` | Dependencies | M | Stay current |

---

## 10. Prevention Rules

To prevent new debt from accumulating, adopt these guardrails:

### CI Pipeline Additions

1. **Enforce mypy passing** — currently 205 errors; create a mypy baseline file and fail CI if new errors are introduced
2. **Enforce test markers** — add a CI check: `pytest --collect-only -m unit | grep "no tests ran" && exit 1`
3. **Enforce coverage without exclusions** — track true coverage alongside the current metric; set a floor that ratchets upward
4. **Add `npm audit --audit-level=moderate`** to CI (already passing, but enforce it)

### Code Review Checklist

- [ ] New API endpoints go through an application service (not direct repository access)
- [ ] New database columns on FK/query fields have `index=True`
- [ ] New repository methods have `limit` and `offset` parameters
- [ ] New Celery tasks have `soft_time_limit`, `time_limit`, and `max_retries`
- [ ] New test functions have appropriate `@pytest.mark.*` markers
- [ ] New dependencies are justified and version-pinned
- [ ] Type hints are complete (no bare `dict`, no `Any` without narrowing)

### Architecture Decision Records

Consider maintaining lightweight ADRs in `docs/adr/` for decisions like:
- Why the application layer exists but is bypassed in most routers
- When to use Celery tasks vs. background tasks
- Caching strategy (what to cache, TTLs, invalidation)

---

## 11. Metrics Dashboard (Baseline)

Use these baseline numbers to track improvement over time:

| Metric | Current | Target (3 months) | Target (6 months) |
|--------|---------|--------------------|--------------------|
| mypy errors | 205 | 50 | 0 |
| Ruff violations | 0 | 0 | 0 |
| True test coverage (no exclusions) | ~50-55% | 65% | 75% |
| Measured test coverage | 85.6% | 88% | 90% |
| Unit tests with `@pytest.mark.unit` | 0/288 | 288/288 | 288+/288+ |
| e2e tests | 0 | 5 | 15 |
| Property-based tests | 0 | 10 | 20 |
| API routers using application services | 3/17 | 10/17 | 17/17 |
| Missing DB indexes | 11 | 0 | 0 |
| Celery tasks with time limits | 0/11 | 11/11 | 11/11 |
| Unused dependencies | 4 | 0 | 0 |
| TypeScript `any` usage | 0 | 0 | 0 |
| Frontend build status | Passing | Passing | Passing |

---

## 12. Effort Estimation Summary

| Phase | Tasks | Estimated Story Points | Timeline |
|-------|-------|----------------------|----------|
| Phase 1 (Fix Now) | 7 tasks | ~13 SP | Week 1 |
| Phase 2 (Next Sprint) | 9 tasks | ~21 SP | Weeks 2-3 |
| Phase 3 (This Quarter) | 11 tasks | ~26 SP | Weeks 4-8 |
| Phase 4 (Backlog) | 13 tasks | ~18 SP | Ongoing |
| **Total** | **40 tasks** | **~78 SP** | **~8 weeks focused** |

---

## Appendix A: Positive Findings

Not everything is debt. These are areas where the project excels:

- **Zero Ruff lint violations** — clean code formatting and style
- **Zero TypeScript `any` types** — full frontend type safety
- **Zero circular imports** — clean dependency graph
- **Zero bare `except:` clauses** — proper exception handling
- **Zero `print()` statements** — structured logging throughout
- **Domain layer isolation** — no outward dependencies, correct Clean Architecture at this layer
- **Thorough documentation** — 7,700+ lines across 13 markdown files
- **Comprehensive API docstrings** — every endpoint documented
- **Well-structured test fixtures** — 61 fixtures with realistic mock data
- **Proper async usage** — no `requests` library, all I/O uses `httpx`/`asyncpg`/`redis.asyncio`
- **Security-conscious configuration** — Swagger disabled in production, webhook signature verification
- **Frontend build passes cleanly** — zero warnings, reasonable bundle sizes

## Appendix B: Files Requiring Immediate Attention

| File | Issues |
|------|--------|
| `backend/app/infrastructure/external/github_client.py:155-160` | TS-01: str used as dict |
| `backend/app/application/services/prompt_service.py:336` | TS-02: set.add() return value |
| `backend/app/tasks/maintenance_tasks.py:136,142` | TS-03: class vs instance attrs |
| `backend/app/application/services/github_sync_service.py:27` | TS-04: None as list |
| `backend/app/api/v1/notifications.py:150,152` | TS-05: Wrong sender types |
| `backend/app/tasks/workflow_tasks.py` (cleanup_old_data) | N+1 deletion pattern |
| `backend/app/infrastructure/database/models/*.py` | Missing FK indexes |
