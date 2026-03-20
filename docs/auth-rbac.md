# 인증 및 권한 시스템 (Auth & RBAC)

캠프보드의 인증 및 역할 기반 접근 제어 시스템 문서

---

## 1. Google OAuth 흐름

### 1.1 개요

Google OAuth 2.0을 통한 사용자 인증 지원. 세 가지 케이스로 분기됨.

```
[사용자] → [Google 로그인 버튼]
              ↓
         [Google OAuth]
              ↓
     [콜백: /api/v1/auth/google/callback]
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 [기존 사용자] [초대된 이메일] [미초대 이메일]
    ↓         ↓              ↓
 [로그인]   [회원가입]     [에러 반환]
```

### 1.2 케이스별 처리

#### Case 1: 기존 사용자 (✅ 구현됨)
- DB에서 이메일로 User 조회
- `is_active` 확인 후 JWT 토큰 발급
- 프론트엔드로 리다이렉트

```python
# backend/app/api/v1/auth.py:581-603
if user:
    if not user.is_active:
        return RedirectResponse(url="...?error=account_disabled")
    tokens = auth_service._generate_tokens(user.id)
    return RedirectResponse(url=f"...?access_token={...}")
```

#### Case 2: 초대된 이메일 (❌ 미구현)
- Invitation 테이블에서 이메일 조회
- `status == PENDING` 및 만료 확인
- 자동으로 User 생성 + CampaignMembership 생성
- Invitation 상태를 `ACCEPTED`로 변경
- JWT 토큰 발급 후 리다이렉트

**구현 필요 위치:** `backend/app/api/v1/auth.py:605-612`

#### Case 3: 미초대 이메일 (✅ 구현됨)
- `invitation_required` 에러와 함께 로그인 페이지로 리다이렉트

```python
return RedirectResponse(
    url=f"...?error=invitation_required&email={email}"
)
```

### 1.3 관련 파일

| 파일 | 역할 |
|------|------|
| `backend/app/api/v1/auth.py` | OAuth 엔드포인트 |
| `frontend/src/app/login/page.tsx` | 로그인 페이지 |
| `frontend/src/app/login/callback/page.tsx` | OAuth 콜백 처리 |

---

## 2. 초대 기반 회원가입 흐름

### 2.1 초대 생성 (관리자)

```
POST /api/v1/invitations
X-Campaign-ID: {campaign_id}
{
  "email": "user@example.com",
  "role_id": 3,
  "department_id": 1,
  "title": "정책팀장"
}
```

- `CAMPAIGN_MANAGE_MEMBERS` 권한 필요
- 7일 유효 토큰 생성

### 2.2 초대 수락 (사용자)

```
1. /invite/{token} 페이지 접속
2. GET /api/v1/invitations/verify/{token} → 초대 유효성 확인
3. POST /api/v1/invitations/accept/{token} → 계정 생성
   {
     "full_name": "홍길동",
     "password": "********"
   }
```

### 2.3 초대 상태

| 상태 | 설명 |
|------|------|
| `PENDING` | 대기 중 (수락 가능) |
| `ACCEPTED` | 수락 완료 |
| `EXPIRED` | 만료됨 |
| `CANCELLED` | 취소됨 |

### 2.4 관련 파일

| 파일 | 역할 |
|------|------|
| `backend/app/models/invitation.py` | Invitation 모델 |
| `backend/app/api/v1/invitations.py` | 초대 API |
| `frontend/src/app/invite/[token]/page.tsx` | 초대 수락 페이지 |

---

## 3. RBAC (역할 기반 접근 제어)

### 3.1 시스템 역할

| 역할 슬러그 | 이름 | 설명 |
|------------|------|------|
| `owner` | Campaign Owner | 모든 권한 |
| `admin` | Administrator | 설정/멤버 관리 |
| `department_head` | Department Head | 부서 관리 |
| `member` | Team Member | 일반 팀원 |
| `volunteer` | Volunteer | 제한된 접근 |

### 3.2 권한 목록 (PERMISSIONS)

```python
# backend/app/models/role.py

class Permission(str, Enum):
    # Campaign
    CAMPAIGN_VIEW = "campaign:view"
    CAMPAIGN_EDIT = "campaign:edit"
    CAMPAIGN_MANAGE_MEMBERS = "campaign:manage_members"
    CAMPAIGN_MANAGE_ROLES = "campaign:manage_roles"
    CAMPAIGN_DELETE = "campaign:delete"

    # Department
    DEPARTMENT_VIEW = "department:view"
    DEPARTMENT_CREATE = "department:create"
    DEPARTMENT_EDIT = "department:edit"
    DEPARTMENT_DELETE = "department:delete"

    # Task
    TASK_VIEW_ALL = "task:view_all"
    TASK_VIEW_DEPARTMENT = "task:view_department"
    TASK_CREATE = "task:create"
    TASK_EDIT_OWN = "task:edit_own"
    TASK_EDIT_ALL = "task:edit_all"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"

    # Board
    BOARD_CREATE = "board:create"
    BOARD_EDIT = "board:edit"
    BOARD_DELETE = "board:delete"

    # Approval
    APPROVAL_REQUEST = "approval:request"
    APPROVAL_DECIDE = "approval:decide"
    APPROVAL_MANAGE_WORKFLOWS = "approval:manage_workflows"

    # Event/Calendar
    EVENT_VIEW = "event:view"
    EVENT_CREATE = "event:create"
    EVENT_EDIT_OWN = "event:edit_own"
    EVENT_EDIT_ALL = "event:edit_all"
    EVENT_DELETE = "event:delete"

    # File
    FILE_UPLOAD = "file:upload"
    FILE_DELETE_OWN = "file:delete_own"
    FILE_DELETE_ALL = "file:delete_all"

    # Others
    WEBHOOK_MANAGE = "webhook:manage"
    AUDIT_VIEW = "audit:view"
```

### 3.3 역할별 권한 매핑

| 권한 | Owner | Admin | Dept Head | Member | Volunteer |
|------|:-----:|:-----:|:---------:|:------:|:---------:|
| campaign:view | ✓ | ✓ | ✓ | ✓ | ✓ |
| campaign:edit | ✓ | ✓ | - | - | - |
| campaign:manage_members | ✓ | ✓ | - | - | - |
| task:view_all | ✓ | ✓ | - | - | - |
| task:view_department | ✓ | ✓ | ✓ | ✓ | ✓ |
| task:create | ✓ | ✓ | ✓ | ✓ | - |
| task:edit_all | ✓ | ✓ | ✓ | - | - |
| task:edit_own | ✓ | ✓ | ✓ | ✓ | ✓ |
| task:delete | ✓ | ✓ | - | - | - |
| approval:decide | ✓ | ✓ | ✓ | - | - |

### 3.4 권한 체크 방법

```python
# 방법 1: 의존성 주입
from app.api.deps import require_permission, CampaignMember

@router.post("/tasks")
async def create_task(
    membership: CampaignMember,
    _: Annotated[None, Depends(require_permission(Permission.TASK_CREATE))],
):
    ...

# 방법 2: 직접 체크
if not membership.has_permission(Permission.TASK_DELETE):
    raise HTTPException(status_code=403, detail="Permission denied")
```

### 3.5 미구현 사항 (🔴)

**부서별 권한 필터링:**
- `TASK_VIEW_DEPARTMENT` 권한 시 자기 부서 작업만 조회해야 함
- 현재: 모든 작업 조회 가능 (버그)

```python
# 구현 필요 위치: backend/app/services/task_service.py
if not member.has_permission(Permission.TASK_VIEW_ALL):
    if member.has_permission(Permission.TASK_VIEW_DEPARTMENT):
        query = query.where(Task.department_id == member.department_id)
```

---

## 4. 백엔드 API 목록

### 4.1 인증 (Auth)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/auth/register` | 회원가입 |
| POST | `/auth/login` | 로그인 |
| POST | `/auth/logout` | 로그아웃 |
| POST | `/auth/refresh` | 토큰 갱신 |
| GET | `/auth/me` | 현재 사용자 정보 |
| PATCH | `/auth/me` | 프로필 수정 |
| POST | `/auth/password/change` | 비밀번호 변경 |
| POST | `/auth/password/reset-request` | 비밀번호 재설정 요청 |
| POST | `/auth/password/reset-confirm` | 비밀번호 재설정 확인 |
| GET | `/auth/google` | Google OAuth 시작 |
| GET | `/auth/google/callback` | Google OAuth 콜백 |
| GET | `/auth/check` | 인증 상태 확인 |

### 4.2 초대 (Invitations)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/invitations` | 초대 생성 |
| GET | `/invitations/verify/{token}` | 초대 검증 |
| POST | `/invitations/accept/{token}` | 초대 수락 |

### 4.3 캠페인 (Campaigns)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/campaigns` | 내 캠페인 목록 |
| POST | `/campaigns` | 캠페인 생성 |
| GET | `/campaigns/{id}` | 캠페인 상세 |
| PATCH | `/campaigns/{id}` | 캠페인 수정 |

### 4.4 멤버 (Members)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/members` | 멤버 목록 |
| POST | `/members` | 기존 사용자 초대 |
| PATCH | `/members/{id}` | 멤버 정보 수정 |
| DELETE | `/members/{id}` | 멤버 제거 |

### 4.5 작업 (Tasks)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/tasks` | 작업 목록 |
| POST | `/tasks` | 작업 생성 |
| GET | `/tasks/{id}` | 작업 상세 |
| PATCH | `/tasks/{id}` | 작업 수정 |
| DELETE | `/tasks/{id}` | 작업 삭제 |
| POST | `/tasks/{id}/move` | 작업 이동 |
| POST | `/tasks/{id}/assignees` | 담당자 추가 |
| DELETE | `/tasks/{id}/assignees/{member_id}` | 담당자 제거 |
| GET | `/tasks/{id}/comments` | 댓글 목록 |
| POST | `/tasks/{id}/comments` | 댓글 추가 |
| PATCH | `/tasks/{id}/comments/{comment_id}` | 댓글 수정 |
| DELETE | `/tasks/{id}/comments/{comment_id}` | 댓글 삭제 |

### 4.6 결재 (Approvals)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/approvals` | 결재 목록 |
| POST | `/approvals` | 결재 요청 |
| GET | `/approvals/{id}` | 결재 상세 |
| POST | `/approvals/{id}/approve` | 승인 |
| POST | `/approvals/{id}/reject` | 반려 |

---

*마지막 업데이트: 2026-03-20*
