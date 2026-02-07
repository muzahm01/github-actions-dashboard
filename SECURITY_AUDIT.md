# Security Audit Report: GitHub Actions Dashboard

**Date:** 2026-02-07
**Scope:** Full codebase review (backend, frontend, Docker, CI/CD)
**Overall Assessment:** MODERATE RISK — Good security fundamentals with critical gaps in authentication enforcement

---

## Executive Summary

The application demonstrates strong security practices in several areas: HMAC-SHA256 webhook validation, parameterized SQL queries, CSP security headers, and SSRF protection. However, the most significant finding is that **API key authentication is defined but never enforced on any endpoint**, leaving all data and operations publicly accessible. Combined with hardcoded default credentials and an authentication bypass in development mode, this represents a critical risk if deployed without careful configuration.

---

## CRITICAL Findings

### 1. API Endpoints Have No Authentication Enforced

**Severity:** CRITICAL
**Files:** All routers in `backend/app/api/v1/`

The `require_api_key` dependency is defined at `backend/app/api/v1/security.py:64` but never applied to any endpoint. Every data endpoint — repositories, workflows, runs, jobs, logs, analysis, search, notifications, prompts — is publicly accessible.

```python
# security.py:64 — defined but unused
require_api_key = Depends(verify_api_key)

# Example: no auth dependency on endpoints
@router.post("/analyze")
async def analyze_error(
    request: AnalysisRequest,
    db: Annotated[AsyncSession, Depends(get_db)],  # no require_api_key
) -> dict:
```

**Impact:** Anyone with network access can read all repository data, trigger LLM analysis (incurring API costs), configure notification webhooks, and modify prompt templates.

**Remediation:** Add `require_api_key` as a dependency to all data-access endpoints. Consider applying it at the router level for broad coverage.

---

### 2. Hardcoded Default Credentials in Source Code

**Severity:** CRITICAL
**Files:** `backend/app/config.py`, `docker-compose.yml`

| Secret | Default Value | Location |
|--------|--------------|----------|
| `postgres_password` | `gha_secret` | `config.py:28`, `docker-compose.yml:8,50,90,118` |
| `secret_key` | `change-me-in-production` | `config.py:75`, `docker-compose.yml:60` |
| `redis_password` | `redis_secret` | `docker-compose.yml:26` |
| Grafana admin password | `admin` | `docker-compose.yml:157` |

These defaults are used as fallbacks (`${VAR:-default}`) in docker-compose, meaning any deployment without a `.env` file runs with known credentials. The application only issues `warnings.warn()` in production (`main.py:31-37`), it does not refuse to start.

**Remediation:** In production mode, fail startup if any of these secrets retain their default values. Remove default fallbacks from docker-compose for sensitive values.

---

### 3. Authentication Bypass in Development Mode

**Severity:** CRITICAL (if accidentally deployed)
**File:** `backend/app/api/v1/security.py:40-45`

```python
if settings.environment in ("development", "testing") and settings.secret_key in (
    "change-me-in-production", "",
):
    return "dev-bypass"
```

Combined with Finding #2 (default `secret_key` and default `environment = "development"`), a misconfigured production deployment silently skips all API key validation. The same bypass applies to WebSocket token validation (`backend/app/infrastructure/websocket/manager.py`).

**Remediation:** Consider requiring an explicit opt-in flag (e.g., `ENABLE_DEV_AUTH_BYPASS=true`) rather than inferring from environment + default secret values.

---

### 4. Webhook Endpoint Crashes on Empty Secret

**Severity:** CRITICAL
**File:** `backend/app/api/v1/webhooks.py:38`

When `github_webhook_secret` is empty (the default), `GitHubWebhookValidator.__init__` raises `ValueError`. This is caught by the generic exception handler and returns a 500 Internal Server Error. The application starts successfully (`main.py:38-43` only warns), so this is a runtime crash on webhook receipt rather than a startup failure.

**Remediation:** Either fail startup when `github_webhook_secret` is empty in production, or handle the `ValueError` gracefully in the webhook endpoint.

---

## HIGH Findings

### 5. LLM Prompt Injection via GitHub Metadata

**Severity:** HIGH
**File:** `backend/app/infrastructure/external/llm_client.py:110-114`

```python
prompt = ERROR_ANALYSIS_PROMPT.format(
    log_content=truncated_log,
    framework=framework,
    job_name=job_name,
)
```

The `framework` and `job_name` values originate from GitHub API data. An attacker who controls a GitHub workflow could craft job names or log output to manipulate the LLM prompt.

**Remediation:** Sanitize or escape user-controlled values before prompt interpolation. Consider structural separation (e.g., XML tags or system/user message boundaries) for untrusted content.

---

### 6. Frontend Stores Credentials in localStorage

**Severity:** HIGH
**File:** `frontend/src/api/client.ts:33-40`

```typescript
const token = localStorage.getItem('auth_token')
const apiKey = localStorage.getItem('api_key')
```

`localStorage` is accessible to any JavaScript on the same origin. If an XSS vulnerability is introduced (even through a third-party dependency), stored tokens are immediately exfiltable.

**Remediation:** Use httpOnly cookies for token storage, which are not accessible to JavaScript.

---

### 7. No Authorization / RBAC

**Severity:** HIGH
**Scope:** Entire application

There is no concept of users, roles, or permissions. A single shared API key grants full access to all operations including triggering LLM analysis (cost implication), configuring webhooks, and modifying prompt templates.

**Remediation:** Implement role-based access control if multi-user access is planned. At minimum, separate read-only and admin API keys.

---

### 8. In-Memory Rate Limiting Not Scalable

**Severity:** HIGH
**File:** `backend/app/api/v1/security.py:109`

```python
_rate_limit_buckets: dict[str, tuple[float, float]] = {}
```

Rate limit state is process-local. It resets on restart, is not shared across workers, and grows unboundedly (no eviction of stale IPs).

**Remediation:** Use Redis for rate limit state storage, with TTL-based key expiration.

---

## MEDIUM Findings

### 9. SSRF Validation Gaps

**File:** `backend/app/api/v1/security.py:165-196`

The `validate_webhook_url` function has good coverage but gaps remain:
- DNS rebinding: validates hostname at configuration time, but hostname could resolve to an internal IP at request time
- Allows `http://` scheme, enabling unencrypted webhook delivery
- Does not resolve and re-check IP at connection time

**Remediation:** Validate resolved IP at connection time, not just at configuration time. Consider requiring HTTPS for all webhook URLs.

---

### 10. No Request Body Size Limits

**Files:** `backend/app/api/v1/webhooks.py:35`, `backend/app/main.py`

```python
payload = await request.body()  # No size limit
```

No `max_body_size` is configured. An attacker could send extremely large payloads to exhaust memory.

**Remediation:** Configure request body size limits in the ASGI server or middleware.

---

### 11. No CSRF Protection

**Scope:** Backend API + Frontend

State-changing operations (POST/PUT/DELETE) have no CSRF token mechanism. With `allow_credentials=True` (`main.py:95`), a misconfigured `cors_origins` could enable cross-origin attacks.

**Remediation:** Add CSRF token headers for state-changing operations, or ensure CORS origins are strictly controlled.

---

### 12. Error Message Leakage in LLM Client

**File:** `backend/app/infrastructure/external/llm_client.py:159`

```python
logger.error(f"Claude API error: {e}")
raise LLMError(f"Claude API error: {e}", provider="claude") from e
```

The exception object could contain API key fragments or sensitive data depending on the SDK's error formatting.

**Remediation:** Log the error type and message separately; avoid passing raw exception objects into user-facing error messages.

---

### 13. Unsanitized Log Content Storage

**File:** `backend/app/tasks/workflow_tasks.py`

Workflow logs from GitHub are stored in the database without filtering. CI logs may contain leaked secrets (API keys, passwords in CI output).

**Remediation:** Apply secret detection/redaction before storing logs.

---

### 14. Docker Configuration Issues

**File:** `docker-compose.yml`

- API service uses `--reload` flag (line 71) — development-only feature
- Source code mounted as volume (lines 68-69) — exposes source in container
- Redis healthcheck uses `ping` without authentication (line 32)
- API port `8000` bound to `0.0.0.0` (line 62) unlike postgres/redis which bind to `127.0.0.1`

**Remediation:** Create a separate `docker-compose.prod.yml` without development overrides. Bind API port to `127.0.0.1` and use a reverse proxy.

---

### 15. No Frontend Route Guards

**File:** `frontend/src/router/index.ts`

No authentication guards on any route. All views are accessible without authentication.

**Remediation:** Add navigation guards that check for valid authentication before rendering protected views.

---

## LOW Findings

### 16. Console Error Logging in Frontend

**File:** `frontend/src/stores/dashboard.ts:45,56,64`

`console.error()` calls could expose API error details in production browser consoles.

---

### 17. No Webhook Replay Window Limit

The Redis idempotency store uses a 24-hour TTL. Webhook replays after 24 hours would be accepted.

---

### 18. OpenAPI Docs Exposed in Non-Production

**File:** `backend/app/main.py:78-80`

API documentation at `/docs` and `/redoc` exposes the full API surface in development/testing.

---

## Security Strengths

| Area | Implementation | Location |
|------|---------------|----------|
| Webhook HMAC-SHA256 | Constant-time `hmac.compare_digest`, proper prefix validation | `webhook_processor.py:46-73` |
| SQL injection prevention | SQLAlchemy ORM with parameterized queries; LIKE pattern escaping | `security.py:204-206`, all repos |
| Security headers | CSP, HSTS (prod), X-Frame-Options DENY, Permissions-Policy | `security.py:72-101` |
| Error information hiding | Generic 500 responses; server-side-only stack traces | `main.py:115-122` |
| GitHub client logging | Explicitly avoids logging response bodies | `github_client.py:112` |
| No command injection | No `subprocess`, `os.system`, `eval`, `exec` usage | Entire codebase |
| No path traversal | No filesystem operations with user input | Entire codebase |
| No XSS in frontend | No `v-html`, `innerHTML`, or unsafe rendering | All Vue components |
| Celery serialization | JSON only, no pickle deserialization | `celery_app.py:22-23` |
| Non-root Docker | Backend runs as `appuser` | `backend/Dockerfile` |
| Webhook idempotency | Atomic Redis `SET NX` prevents duplicates | `webhook_processor.py:149-177` |
| API docs disabled in prod | `/docs`, `/redoc`, `/openapi.json` all `None` in production | `main.py:78-80` |

---

## Priority Remediation Order

1. **Add `require_api_key` to all data endpoints** (Finding #1)
2. **Fail startup on default secrets in production** (Findings #2, #3)
3. **Enforce non-empty webhook secret in production** (Finding #4)
4. **Sanitize LLM prompt inputs** (Finding #5)
5. **Move token storage to httpOnly cookies** (Finding #6)
6. **Add request body size limits** (Finding #10)
7. **Move rate limiting to Redis** (Finding #8)
8. **Add DNS rebinding protection** (Finding #9)
9. **Bind API port to 127.0.0.1 in docker-compose** (Finding #14)
