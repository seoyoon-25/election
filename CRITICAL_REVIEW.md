# Critical Review: Campaign Operations OS

**Date:** 2026-03-19
**Reviewer:** Claude Code
**Scope:** /var/www/election (Backend + Frontend + Infrastructure)

---

## Executive Summary

The Campaign Operations OS is a multi-tenant SaaS platform for election campaign management built with FastAPI (backend) and Next.js (frontend). While the architecture is fundamentally sound with good separation of concerns, **several critical security and data isolation issues must be addressed before production deployment**.

**Overall Assessment:** The codebase shows thoughtful design patterns but lacks enforcement mechanisms for its security model. The multi-tenancy infrastructure exists but isn't actively protecting data.

---

## 1. Architecture & Boundaries

### 1.1 Multi-Tenancy Implementation

#### Strengths
- **TenantMixin Pattern:** All tenant-scoped models inherit from `TenantMixin`, providing consistent `campaign_id` columns with proper indexing.
- **Header-Based Campaign Context:** `X-Campaign-ID` header used for campaign selection with membership validation.
- **Infrastructure for RLS:** Code includes `set_tenant_context()` for PostgreSQL Row-Level Security.

#### Critical Issues

**Issue 1.1.1: Row-Level Security Policies Not Implemented**
- **Location:** `backend/alembic/versions/*.py`
- **Impact:** HIGH - Complete tenant data isolation failure possible
- **Details:** The codebase sets PostgreSQL session variables via `set_tenant_context()` but **no RLS policies are defined** in any migration. This means the tenant context has zero effect on query filtering.
- **Example:** If any service query forgets to include `WHERE campaign_id = ?`, all campaigns' data is returned.
- **Recommendation:** Add a migration creating RLS policies for all tenant tables:
  ```sql
  ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
  CREATE POLICY tenant_isolation_tasks ON tasks
    USING (campaign_id = current_setting('app.current_campaign_id')::int);
  ```

**Issue 1.1.2: Inconsistent Campaign ID Validation**
- **Location:** `backend/app/services/task_service.py:603-618`
- **Impact:** HIGH - Cross-tenant data manipulation
- **Details:** The `delete_comment()` method queries by `comment_id` alone without validating that the comment belongs to a task in the current campaign.
- **Example:** A user in Campaign A could potentially delete a comment from Campaign B if they guess the comment ID.
- **Recommendation:** Add campaign validation to all entity operations:
  ```python
  async def delete_comment(self, comment_id: int) -> None:
      result = await self.db.execute(
          select(TaskComment)
          .join(Task)
          .where(
              TaskComment.id == comment_id,
              Task.campaign_id == self.campaign_id  # Add this
          )
      )
  ```

**Issue 1.1.3: User Model Exposes All Campaigns**
- **Location:** `backend/app/models/user.py`
- **Impact:** MEDIUM - Information disclosure
- **Details:** The `User.campaigns` property returns all campaign memberships without filtering, potentially exposing campaign names across tenants if eagerly loaded.
- **Recommendation:** Remove the property or make it campaign-context-aware.

### 1.2 Service Layer Separation

#### Strengths
- Clean three-tier architecture: API (routing) → Services (business logic) → Models (data)
- Services receive database session and membership context via dependency injection
- Pydantic schemas validate all API inputs/outputs

#### Issues

**Issue 1.2.1: Business Logic in API Layer**
- **Location:** `backend/app/api/v1/tasks.py:130-145`
- **Impact:** LOW - Maintainability
- **Details:** Task listing endpoint performs loop-based detail fetching that should be in the service layer.
- **Recommendation:** Move complex orchestration to service methods.

---

## 2. Security

### 2.1 Authentication & JWT

#### Strengths
- Bcrypt password hashing with 12 rounds
- Short-lived access tokens (30 min) with longer refresh tokens (7 days)
- HTTP Bearer scheme properly implemented

#### Critical Issues

**Issue 2.1.1: No Token Revocation/Blacklist**
- **Location:** `backend/app/api/v1/auth.py:181-183`
- **Impact:** CRITICAL - Compromised tokens remain valid
- **Details:** The logout endpoint is a no-op (`return None`). Comment states "In production, you'd want to blacklist the refresh token" but this is not implemented.
- **Example:** If a user's token is stolen, the attacker has full access for up to 7 days.
- **Recommendation:** Implement Redis-based token blacklist:
  ```python
  async def logout(token: str, redis: Redis):
      await redis.setex(f"blacklist:{token}", 7*24*3600, "1")
  ```

**Issue 2.1.2: Development Secrets in Configuration**
- **Location:** `backend/.env`, `backend/app/config.py:47-49`
- **Impact:** CRITICAL - Production security breach
- **Details:**
  - JWT secret: `dev-secret-key-for-local-development-32ch`
  - MinIO credentials: `minioadmin:minioadmin`
  - Config has defaults like `"your-super-secret-key-change-in-production"`
- **Recommendation:**
  1. Remove all default secrets from `config.py`
  2. Add validation that raises error if secrets not provided in production
  3. Use proper secrets management (AWS Secrets Manager, Vault, etc.)

**Issue 2.1.3: Password Reset Token Exposed in Response**
- **Location:** `backend/app/api/v1/auth.py` (password reset endpoint)
- **Impact:** HIGH - Account takeover in development mode
- **Details:** Debug response includes `"debug_token": token` with comment "Remove this in production!"
- **Recommendation:** Remove debug token exposure entirely; implement proper email delivery.

**Issue 2.1.4: Token Encryption Key Optional**
- **Location:** `backend/app/config.py:102`
- **Impact:** HIGH - Google OAuth tokens stored unencrypted
- **Details:** `token_encryption_key: Optional[str] = None` means OAuth tokens may be stored in plaintext.
- **Recommendation:** Make encryption key required when Google OAuth is configured.

### 2.2 Authorization & RBAC

#### Strengths
- Comprehensive permission system with 20+ granular permissions
- System roles with sensible defaults (Owner, Admin, Member, Volunteer)
- `require_permission()` dependency for endpoint protection

#### Issues

**Issue 2.2.1: Department-Scoped Permissions Not Enforced**
- **Location:** `backend/app/services/task_service.py`
- **Impact:** HIGH - Privilege escalation
- **Details:** Permissions like `TASK_VIEW_DEPARTMENT` and `TASK_EDIT_OWN` are defined but not checked in service methods. Department heads can see all tasks, not just their department's.
- **Recommendation:** Add department filtering in `list_tasks()`:
  ```python
  if Permission.TASK_VIEW_ALL not in member.permissions:
      if Permission.TASK_VIEW_DEPARTMENT in member.permissions:
          query = query.where(Task.department_id == member.department_id)
  ```

**Issue 2.2.2: Approval Workflow Authorization Gap**
- **Location:** `backend/app/services/approval_service.py`
- **Impact:** MEDIUM - Invalid approvers
- **Details:** Approval steps can reference `approver_id` that becomes invalid if member is removed. No validation that approver still has required role.
- **Recommendation:** Validate approver membership and role at decision time.

**Issue 2.2.3: `is_department_head` Flag Unused**
- **Location:** `backend/app/models/campaign.py`
- **Impact:** MEDIUM - Feature incomplete
- **Details:** `CampaignMembership.is_department_head` exists but is never checked in authorization logic.
- **Recommendation:** Use flag in permission checks for department-level operations.

### 2.3 Data Protection

**Issue 2.3.1: CORS Allows All Methods/Headers**
- **Location:** `backend/app/main.py:53-54`
- **Impact:** MEDIUM - Overly permissive
- **Details:** `allow_methods=["*"]` and `allow_headers=["*"]` are too broad for production.
- **Recommendation:** Explicitly list allowed methods (`GET`, `POST`, `PATCH`, `DELETE`) and headers.

**Issue 2.3.2: No File Upload Validation**
- **Location:** `backend/app/config.py:68-82`
- **Impact:** MEDIUM - Malicious file uploads
- **Details:** `allowed_file_types` is configured but not enforced in API layer. Files go directly to S3.
- **Recommendation:** Validate MIME type and file extension before S3 upload.

**Issue 2.3.3: Exception Details Exposed in Debug Mode**
- **Location:** `backend/app/main.py:62-70`
- **Impact:** LOW - Information disclosure
- **Details:** Full exception messages returned when `debug=True`. Could leak stack traces with sensitive paths.
- **Recommendation:** Even in debug, sanitize exception messages.

---

## 3. Data Model & Performance

### 3.1 Model Design

#### Strengths
- Proper use of foreign keys with `ondelete="CASCADE"` for parent-child relationships
- Unique constraints preventing duplicate memberships
- Comprehensive audit trail via `TaskHistory`
- Soft delete patterns with `is_active` flags

#### Issues

**Issue 3.1.1: Circular Department Hierarchy Possible**
- **Location:** `backend/app/models/campaign.py` (Department model)
- **Impact:** HIGH - Application crash
- **Details:** `Department.parent_id` self-reference has no constraint preventing cycles. The `full_path` property would infinite loop.
- **Recommendation:** Add database constraint or application validation:
  ```sql
  ALTER TABLE departments ADD CONSTRAINT no_circular_hierarchy
    CHECK (id != parent_id);
  -- Plus application-level ancestry check
  ```

**Issue 3.1.2: Orphaned Task Creator References**
- **Location:** `backend/app/models/task.py:60`
- **Impact:** LOW - Audit trail loss
- **Details:** `Task.created_by_id` uses `ondelete="SET NULL"`. When member removed, task creator becomes NULL.
- **Recommendation:** Keep member records with `is_active=False` instead of deleting.

**Issue 3.1.3: Approval Request Expiry Not Enforced**
- **Location:** `backend/app/models/approval.py`
- **Impact:** MEDIUM - Stuck workflows
- **Details:** `ApprovalRequest.expires_at` is set but never checked. Expired requests remain PENDING forever.
- **Recommendation:** Add background job to mark expired requests:
  ```python
  # Celery/APScheduler task
  async def expire_approval_requests():
      await db.execute(
          update(ApprovalRequest)
          .where(ApprovalRequest.expires_at < now(), ApprovalRequest.status == "pending")
          .values(status="expired")
      )
  ```

### 3.2 Indexing & Query Performance

#### Current Indexes
- `campaign_id` on all tenant tables (good)
- Composite `(campaign_id, board_id)` on tasks (good)
- `(column_id, sort_order)` on tasks (good)

#### Missing Indexes

**Issue 3.2.1: Missing Compound Indexes**
- **Impact:** MEDIUM - Slow queries at scale
- **Details:**
  - No `(campaign_id, status)` on approval_requests (common filter)
  - No `(task_id, created_at)` on task_history (pagination)
  - No `(campaign_id, assignee_id)` on task_assignments (my tasks query)
- **Recommendation:** Add migration with compound indexes.

**Issue 3.2.2: N+1 Query in Task Listing**
- **Location:** `backend/app/api/v1/tasks.py:132`
- **Impact:** MEDIUM - Performance degradation
- **Details:** Loop calls `task_service.get_task()` for each task to get details.
- **Recommendation:** Use batch loading or return details in initial query.

**Issue 3.2.3: No Pagination on List Endpoints**
- **Location:** Multiple endpoints in `tasks.py`, `approvals.py`
- **Impact:** HIGH - Memory exhaustion DoS
- **Details:** `list_tasks()`, `list_members()` return all records without limit.
- **Recommendation:** Add `page` and `page_size` parameters with defaults (e.g., 20 items).

**Issue 3.2.4: Eager Loading Overhead**
- **Location:** `backend/app/models/campaign.py`, `user.py`
- **Impact:** MEDIUM - Unnecessary data loading
- **Details:** Campaign model uses `lazy="selectin"` loading for memberships/roles/departments. Even when only needing `slug`, all relationships load.
- **Recommendation:** Change to `lazy="select"` (lazy loading) by default; eager load explicitly when needed.

### 3.3 Data Consistency

**Issue 3.3.1: Inconsistent Transaction Handling**
- **Location:** Various service methods
- **Impact:** MEDIUM - Partial updates possible
- **Details:** Some operations use `await db.flush()`, others don't. Multi-step operations (create task + assign + log history) lack explicit transaction boundaries.
- **Recommendation:** Wrap multi-step operations in explicit transactions:
  ```python
  async with db.begin():
      task = await create_task(...)
      await add_assignee(...)
      await add_history(...)
  ```

**Issue 3.3.2: Google Calendar Sync Race Conditions**
- **Location:** `backend/app/services/calendar_service.py`
- **Impact:** MEDIUM - Duplicate events
- **Details:** No locking or idempotency keys for calendar sync operations. Concurrent syncs could create duplicates.
- **Recommendation:** Use distributed locks (Redis) for sync operations.

---

## 4. DevOps & Developer Experience

### 4.1 Docker Configuration

#### Strengths
- Non-root user (`appuser`) in backend container
- Health checks on all services
- Read-only volume mounts for source code
- Proper service dependencies

#### Issues

**Issue 4.1.1: Secrets in docker-compose.yml**
- **Location:** `docker-compose.yml:10-12, 70-71`
- **Impact:** HIGH - Credentials in version control
- **Details:** PostgreSQL and MinIO credentials hardcoded in docker-compose.
- **Recommendation:** Use `.env` file or Docker secrets:
  ```yaml
  services:
    postgres:
      environment:
        POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      secrets:
        - db_password
  ```

**Issue 4.1.2: No Separate Production Configuration**
- **Location:** `docker-compose.yml`
- **Impact:** MEDIUM - Environment parity issues
- **Details:** Single docker-compose used for dev and production. Hot-reload mounts inappropriate for production.
- **Recommendation:** Create `docker-compose.prod.yml` with production settings.

**Issue 4.1.3: Redis Without Password**
- **Location:** `docker-compose.yml:27-37`
- **Impact:** MEDIUM - Unauthorized access
- **Details:** Redis runs without authentication. Accessible to any network user.
- **Recommendation:** Configure Redis password:
  ```yaml
  command: redis-server --requirepass ${REDIS_PASSWORD}
  ```

### 4.2 Local Development

#### Strengths
- Makefile with common commands
- Hot-reload for both backend and frontend
- Alembic migrations run on container startup

#### Issues

**Issue 4.2.1: entrypoint.sh Redis Wait Simplified**
- **Location:** `backend/entrypoint.sh:29-33`
- **Impact:** LOW - Startup race conditions
- **Details:** Redis wait is just `sleep 5` instead of actual connectivity check.
- **Recommendation:** Use proper health check or retry loop.

**Issue 4.2.2: Port Conflicts Not Documented**
- **Location:** `docker-compose.yml`
- **Impact:** LOW - Developer friction
- **Details:** Uses ports 5432, 6379, 3000 which commonly conflict with local services.
- **Recommendation:** Document port requirements or use non-standard ports.

### 4.3 Testing

#### Current State
- Test files exist for tasks, calendar, approvals
- pytest-asyncio configured
- Fixtures for common entities

#### Issues

**Issue 4.3.1: No Multi-Tenancy Isolation Tests**
- **Impact:** HIGH - Critical security untested
- **Details:** No tests verifying that Campaign A cannot access Campaign B's data.
- **Recommendation:** Add cross-tenant access tests for all entities.

**Issue 4.3.2: No Authorization Tests**
- **Impact:** HIGH - Permission system untested
- **Details:** No tests verifying permission checks (e.g., Volunteer cannot delete tasks).
- **Recommendation:** Add tests for each permission with allowed/denied scenarios.

**Issue 4.3.3: No Concurrent Access Tests**
- **Impact:** MEDIUM - Race conditions untested
- **Details:** No tests for concurrent task updates, approval decisions, etc.
- **Recommendation:** Add async tests with concurrent operations.

---

## 5. Frontend Considerations

### 5.1 API Client

**Issue 5.1.1: Tokens Stored in localStorage**
- **Location:** `frontend/src/lib/api.ts:27-37`
- **Impact:** MEDIUM - XSS vulnerability
- **Details:** JWT tokens stored in `localStorage`, vulnerable to XSS attacks.
- **Recommendation:** Use httpOnly cookies for token storage, or implement token refresh with short-lived memory-only access tokens.

**Issue 5.1.2: No CSRF Protection**
- **Location:** `frontend/src/lib/api.ts`
- **Impact:** MEDIUM - CSRF attacks possible
- **Details:** API calls don't include CSRF tokens.
- **Recommendation:** Implement CSRF token validation for state-changing requests.

### 5.2 Error Handling

**Issue 5.2.1: Generic Error Messages**
- **Location:** `frontend/src/lib/api.ts:55-57`
- **Impact:** LOW - Poor UX
- **Details:** Errors fall back to "Request failed" without context.
- **Recommendation:** Implement proper error categorization and user-friendly messages.

---

## Prioritized TODO List

### High Priority (Address Before Production)

| # | Issue | Category | Effort |
|---|-------|----------|--------|
| 1 | Implement PostgreSQL Row-Level Security policies | Security | Medium |
| 2 | Add token blacklist/revocation on logout | Security | Low |
| 3 | Remove development secrets from config defaults | Security | Low |
| 4 | Fix campaign_id validation in delete_comment and similar | Multi-tenancy | Low |
| 5 | Add pagination to all list endpoints | Performance | Medium |
| 6 | Implement approval request expiry background job | Data Integrity | Medium |
| 7 | Add multi-tenancy isolation tests | Testing | Medium |
| 8 | Move secrets to external secrets manager | DevOps | Medium |
| 9 | Add Redis password authentication | Security | Low |
| 10 | Enforce department-scoped permissions | Authorization | Medium |

### Medium Priority (Address Soon)

| # | Issue | Category | Effort |
|---|-------|----------|--------|
| 11 | Add compound database indexes | Performance | Low |
| 12 | Prevent circular department hierarchy | Data Integrity | Low |
| 13 | Fix N+1 query in task listing | Performance | Low |
| 14 | Add file upload MIME validation | Security | Low |
| 15 | Create production docker-compose | DevOps | Medium |
| 16 | Add authorization/permission tests | Testing | Medium |
| 17 | Implement CSRF protection | Security | Medium |
| 18 | Use httpOnly cookies for tokens | Security | Medium |
| 19 | Add explicit transaction boundaries | Data Integrity | Medium |
| 20 | Restrict CORS methods/headers | Security | Low |

### Low Priority (Nice to Have)

| # | Issue | Category | Effort |
|---|-------|----------|--------|
| 21 | Change eager loading to lazy by default | Performance | Low |
| 22 | Move business logic from API to service layer | Architecture | Medium |
| 23 | Add structured logging | DevOps | Medium |
| 24 | Improve error messages in frontend | UX | Low |
| 25 | Fix entrypoint.sh Redis connectivity check | DevOps | Low |
| 26 | Document port requirements | DevOps | Low |
| 27 | Add concurrent access tests | Testing | Medium |
| 28 | Remove `is_department_head` or implement it | Code Quality | Low |

---

## Conclusion

The Campaign Operations OS has a solid architectural foundation but requires significant security hardening before production use. The most critical issues are:

1. **RLS not implemented** - The multi-tenancy model exists but doesn't actually protect data
2. **No token revocation** - Compromised sessions cannot be terminated
3. **Secrets in code** - Development credentials could leak to production

Addressing the High Priority items above would bring the application to a production-ready state. The codebase is well-organized and the fixes are straightforward to implement.
