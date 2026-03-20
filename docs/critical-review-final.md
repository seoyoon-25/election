# CampBoard 크리티컬 리뷰 최종 보고서

> **리뷰 일자:** 2026-03-20
> **프로젝트:** CampBoard (캠프보드) - 선거 캠페인 운영 관리 시스템
> **리뷰어:** Claude (Opus 4.5)

---

## 목차

1. [보안 (Security)](#1-보안-security)
2. [데이터 무결성 (Data Integrity)](#2-데이터-무결성-data-integrity)
3. [에러 처리 (Error Handling)](#3-에러-처리-error-handling)
4. [성능 (Performance)](#4-성능-performance)
5. [UX/UI](#5-uxui)
6. [코드 품질 (Code Quality)](#6-코드-품질-code-quality)
7. [운영 안정성 (Operations)](#7-운영-안정성-operations)
8. [요약](#8-요약)

---

## 1. 보안 (Security)

### 1.1 인증/인가

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| JWT 토큰 만료 | ✅ 양호 | `backend/app/core/security.py:90,123` | Access: 30분, Refresh: 7일로 적절하게 설정됨 | - |
| Refresh 토큰 처리 | ✅ 양호 | `backend/app/services/token_blacklist.py` | Redis 기반 블랙리스트 구현됨 | - |
| Superadmin 엔드포인트 보호 | ✅ 양호 | `backend/app/api/deps.py:201-210` | `require_superadmin` 의존성으로 보호됨 | - |
| Rate Limiting | 🔴 즉시 수정 | `backend/app/config.py:120-121` | 설정만 있고 실제 미들웨어 미적용 | SlowAPI 또는 유사 라이브러리로 rate limiting 미들웨어 추가 |
| 비밀번호 리셋 토큰 노출 | 🔴 즉시 수정 | `backend/app/api/v1/auth.py:363` | `debug_token` 응답에 포함됨 | 해당 라인 제거 |

### 1.2 입력값 검증

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| SQL Injection | ✅ 양호 | `backend/app/services/*` | SQLAlchemy ORM 파라미터화 쿼리 사용 | - |
| XSS 방어 | ✅ 양호 | `frontend/src/components/*` | React JSX 자동 이스케이핑 사용 | - |
| CSRF 방어 | ⚠️ 개선 필요 | `frontend/src/*` | CSRF 토큰 미구현 | Double-Submit Cookie 패턴 구현 |
| Pydantic 검증 | ✅ 양호 | `backend/app/schemas/*.py` | 이메일, 비밀번호 길이 등 검증됨 | - |

### 1.3 민감 정보

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 개발용 시크릿 키 | 🔴 즉시 수정 | `backend/.env:30` | `JWT_SECRET_KEY=dev-secret-key...` 하드코딩 | 프로덕션 배포 전 반드시 변경 |
| MinIO 기본 인증 | ⚠️ 개선 필요 | `docker-compose.yml:92-93` | `minioadmin/minioadmin` 기본값 | 강력한 인증정보로 변경 |
| Google OAuth 정보 | ⚠️ 개선 필요 | `backend/.env:63` | Client ID 하드코딩 | 환경별 분리 관리 |

### 1.4 Google OAuth

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 미초대 이메일 차단 | ✅ 양호 | `backend/app/api/v1/auth.py:607-627` | 초대 없는 이메일 거부 작동함 | - |
| 이메일 열거 취약점 | ⚠️ 개선 필요 | `backend/app/api/v1/auth.py:626` | 오류 메시지에 이메일 노출 | 일반적 오류 메시지로 변경 |
| State 토큰 관리 | ⚠️ 개선 필요 | `backend/app/api/v1/auth.py:437-461` | 메모리 기반 저장, 만료 정리 없음 | Redis 기반으로 전환, TTL 설정 |
| _generate_tokens 메서드 | 🔴 즉시 수정 | `backend/app/api/v1/auth.py:596,661` | 존재하지 않는 메서드 호출 | `create_token_pair()` 메서드로 변경 |

### 1.5 초대 토큰

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 토큰 만료 | ✅ 양호 | `backend/app/models/invitation.py:76` | 7일 만료 설정됨 | - |
| 토큰 재사용 방지 | ✅ 양호 | `backend/app/models/invitation.py:36` | `unique=True` 제약 조건 | - |
| 암호학적 안전성 | ✅ 양호 | `backend/app/models/invitation.py:71` | `secrets.token_urlsafe(32)` 사용 | - |

### 1.6 토큰 저장소

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| localStorage 사용 | 🔴 즉시 수정 | `frontend/src/lib/api.ts:20-42` | XSS 공격 시 토큰 탈취 가능 | httpOnly 쿠키로 전환 |
| OAuth 콜백 토큰 노출 | ⚠️ 개선 필요 | `frontend/src/app/login/callback/page.tsx:12-18` | URL 파라미터로 토큰 전달 | POST 리다이렉트 또는 쿠키 사용 |

### 1.7 CORS 설정

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 메서드/헤더 전체 허용 | ⚠️ 개선 필요 | `backend/app/main.py:61-62` | `allow_methods=["*"]`, `allow_headers=["*"]` | 필요한 메서드/헤더만 명시 |
| Origin 설정 | ✅ 양호 | `backend/.env:17` | 특정 도메인만 허용됨 | - |

---

## 2. 데이터 무결성 (Data Integrity)

### 2.1 DB 트랜잭션

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 자동 커밋/롤백 | ✅ 양호 | `backend/app/database.py:56-73` | 의존성 주입으로 자동 처리 | - |
| 멀티 스텝 작업 | ✅ 양호 | `backend/app/services/campaign_service.py:114-185` | 캠페인 생성 시 원자성 보장 | - |
| flush vs commit 혼용 | ⚠️ 개선 필요 | `backend/app/services/approval_service.py` | 패턴 일관성 부족 | 표준 패턴 정립 필요 |

### 2.2 외래키 제약

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| CASCADE 삭제 | ✅ 양호 | `backend/app/models/membership.py:46,50` | 사용자/캠페인 삭제 시 멤버십 자동 삭제 | - |
| RESTRICT 제약 | ✅ 양호 | `backend/app/models/membership.py:54` | 역할 사용 중 삭제 방지 | - |
| SET NULL 처리 | ✅ 양호 | `backend/app/models/membership.py:58,62,66` | 부서/초대자 삭제 시 NULL 설정 | - |
| 고아 데이터 처리 | ✅ 양호 | `backend/app/models/*.py` | `cascade="all, delete-orphan"` 설정 | - |

### 2.3 중복 데이터 방지

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 이메일 유니크 | ✅ 양호 | `backend/app/models/user.py:44` | `unique=True` 설정 | - |
| 멤버십 유니크 | ✅ 양호 | `backend/app/models/membership.py:123-127` | `(user_id, campaign_id)` 복합 유니크 | - |
| 초대 경쟁 조건 | ⚠️ 개선 필요 | `backend/app/api/v1/invitations.py:139-149` | 중복 체크와 생성이 원자적이지 않음 | UNIQUE WHERE 조건부 제약 추가 |

### 2.4 RLS 정책

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 메인 테이블 RLS | ✅ 양호 | `backend/alembic/versions/20240104_*.py` | 9개 주요 테이블에 RLS 적용 | - |
| 자식 테이블 RLS | ⚠️ 개선 필요 | - | task_assignments, task_comments 등 미적용 | EXISTS 서브쿼리로 RLS 확장 |
| 테넌트 컨텍스트 | ✅ 양호 | `backend/app/database.py:110-143` | `set_tenant_context()` 구현됨 | - |

---

## 3. 에러 처리 (Error Handling)

### 3.1 API 에러 응답

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 전역 예외 핸들러 | ✅ 양호 | `backend/app/main.py:66-84` | 프로덕션/개발 모드 분리 | - |
| HTTP 상태 코드 일관성 | ✅ 양호 | `backend/app/api/v1/*` | 146개 HTTPException 일관적 사용 | - |
| 서비스 예외 클래스 | ✅ 양호 | `backend/app/services/auth_service.py:36-85` | 커스텀 예외 계층 구조 | - |
| Validation 에러 핸들러 | ⚠️ 개선 필요 | `backend/app/main.py` | Pydantic 검증 에러 커스텀 핸들러 없음 | 일관된 에러 포맷 핸들러 추가 |

### 3.2 프론트엔드 에러 처리

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| API 에러 처리 | ✅ 양호 | `frontend/src/lib/api.ts:68-77` | 401 처리, 에러 파싱 구현 | - |
| 네트워크 타임아웃 | 🔴 즉시 수정 | `frontend/src/lib/api.ts:66` | 타임아웃 미설정, 무한 대기 가능 | AbortController로 30초 타임아웃 추가 |
| 재시도 로직 | ⚠️ 개선 필요 | `frontend/src/lib/api.ts` | 네트워크 실패 시 재시도 없음 | 지수 백오프 재시도 구현 |
| Error Boundary | ⚠️ 개선 필요 | `frontend/src/app/*` | React Error Boundary 미구현 | error.tsx 파일 추가 |

### 3.3 빈 상태/로딩 상태

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 로딩 컴포넌트 | ✅ 양호 | `frontend/src/components/common/LoadingState.tsx` | 3가지 variant, 접근성 지원 | - |
| 에러 컴포넌트 | ✅ 양호 | `frontend/src/components/common/ErrorState.tsx` | 재시도 버튼, 접근성 지원 | - |
| 빈 상태 컴포넌트 | ✅ 양호 | `frontend/src/components/common/EmptyState.tsx` | 아이콘, 액션 버튼 지원 | - |
| 멤버 페이지 에러 | 🔴 즉시 수정 | `frontend/src/app/c/[campaignId]/members/page.tsx:35` | 에러 시 console.error만, UI 미표시 | ErrorState 컴포넌트 렌더링 |

---

## 4. 성능 (Performance)

### 4.1 N+1 쿼리

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 결재 요청 목록 | 🔴 즉시 수정 | `backend/app/services/approval_service.py:390-425` | eager loading 없이 관계 접근 | `selectinload()` 추가 |
| 태스크 속성 접근 | ⚠️ 개선 필요 | `backend/app/api/v1/tasks.py:680-682` | `comment_count` 등 계산 시 쿼리 발생 가능 | 관계 미리 로드 확인 |
| Admin 사용자 로딩 | ⚠️ 개선 필요 | `backend/app/api/v1/admin.py:166-170` | 루프 내 User 로딩 | JOIN 쿼리로 최적화 |

### 4.2 인덱스

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 태스크 쿼리 인덱스 | ✅ 양호 | `backend/app/models/task.py` | 복합 인덱스 적절히 설정 | - |
| 멤버십 인덱스 | ✅ 양호 | `backend/app/models/membership.py` | 4개 복합 인덱스 설정 | - |
| Campaign.status | ⚠️ 개선 필요 | `backend/app/models/campaign.py` | 상태 필터링 인덱스 없음 | 인덱스 추가 |
| ApprovalRequest.workflow_id | ⚠️ 개선 필요 | `backend/app/models/approval.py` | 워크플로우 필터링 인덱스 없음 | 인덱스 추가 |

### 4.3 페이지네이션

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 목록 API 페이지네이션 | ✅ 양호 | `backend/app/services/*` | 모든 목록 API에 구현됨 | - |
| 기본/최대 크기 | ✅ 양호 | - | 기본 20, 최대 100으로 제한 | - |

### 4.4 프론트엔드 성능

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| React.memo | 🔴 즉시 수정 | `frontend/src/components/*` | 48+ 컴포넌트에 memo 미사용 | 주요 컴포넌트에 React.memo 적용 |
| useMemo/useCallback | 🔴 즉시 수정 | `frontend/src/app/c/[campaignId]/dashboard/page.tsx:88-97` | 매 렌더링마다 필터링 재계산 | useMemo로 최적화 |
| 이미지 최적화 | ⚠️ 개선 필요 | `frontend/src/components/common/UserAvatar.tsx` | Next.js Image 미사용 | next/image 컴포넌트 사용 |
| 가상화 | ⚠️ 개선 필요 | `frontend/src/components/tasks/TaskBoard.tsx` | 대량 태스크 시 DOM 과부하 | react-window 또는 유사 라이브러리 적용 |

---

## 5. UX/UI

### 5.1 역할별 접근 제어

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 사이드바 역할 분기 | ✅ 양호 | `frontend/src/components/layout/Sidebar.tsx:44,153-187` | admin 메뉴 조건부 표시 | - |
| 헤더 superadmin 버튼 | ✅ 양호 | `frontend/src/components/layout/Header.tsx:68-75` | superadmin만 표시 | - |
| Admin 레이아웃 보호 | ✅ 양호 | `frontend/src/app/admin/layout.tsx:40-60` | 인증 + superadmin 체크 | - |
| 서버사이드 라우트 보호 | ⚠️ 개선 필요 | `frontend/src/app/*` | 클라이언트 사이드만 체크 | middleware.ts 구현 |

### 5.2 폼 유효성 검사

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 로그인 폼 | ✅ 양호 | `frontend/src/app/login/page.tsx:162,176` | required 속성, 에러 표시 | - |
| 캠페인 생성 폼 | ✅ 양호 | `frontend/src/app/campaigns/new/page.tsx:116-129` | 필수 필드 검증 | - |
| 초대 수락 폼 | ✅ 양호 | `frontend/src/app/invite/[token]/page.tsx:468-478` | 비밀번호 일치 실시간 표시 | - |
| 비밀번호 변경 폼 | ✅ 양호 | `frontend/src/app/settings/page.tsx:48-62` | 길이, 일치, 동일성 검증 | - |

### 5.3 피드백

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 성공/실패 알림 | ⚠️ 개선 필요 | `frontend/src/*` | 폼별 인라인 알림만, 토스트 없음 | 토스트 알림 시스템 추가 |
| 로딩 버튼 상태 | ✅ 양호 | `frontend/src/app/login/page.tsx:182-187` | 스피너 + 텍스트 변경 | - |
| 파괴적 작업 확인 | ⚠️ 개선 필요 | `frontend/src/app/c/[campaignId]/approvals/page.tsx:144-147` | 승인/거부 확인 다이얼로그 없음 | 확인 다이얼로그 추가 |

### 5.4 반응형

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 모바일 네비게이션 | ✅ 양호 | `frontend/src/components/layout/Header.tsx:50-59` | 햄버거 메뉴, aria 속성 | - |
| 대시보드 그리드 | ✅ 양호 | `frontend/src/app/c/[campaignId]/dashboard/page.tsx:153,185` | 반응형 그리드 적용 | - |
| 테이블 반응형 | ⚠️ 개선 필요 | `frontend/src/app/c/[campaignId]/members/page.tsx:72-120` | 모바일에서 오버플로우 가능 | `overflow-x-auto` 래퍼 추가 |

### 5.5 한국어 일관성

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 로그인/설정/대시보드 | ✅ 양호 | - | 모두 한국어 | - |
| 멤버 페이지 | 🔴 즉시 수정 | `frontend/src/app/c/[campaignId]/members/page.tsx:55,58,65,75-78` | "Team Members", "Invite Member" 등 영어 | 한국어로 변경 |
| 결재 페이지 | 🔴 즉시 수정 | `frontend/src/app/c/[campaignId]/approvals/page.tsx:13-17,79,110-114` | "All", "Pending", "Approved" 등 영어 | 한국어로 변경 |
| 날짜 포맷 | ⚠️ 개선 필요 | `frontend/src/app/c/[campaignId]/approvals/page.tsx:130` | 영어 날짜 포맷 사용 | `toLocaleDateString('ko-KR')` 사용 |

---

## 6. 코드 품질 (Code Quality)

### 6.1 중복 코드

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| Admin 목록 관리 | ⚠️ 개선 필요 | `frontend/src/app/admin/{users,campaigns,invitations}/page.tsx` | 300+ 라인 중복 (상태, fetch, 검색, CSV 내보내기) | `useAdminListManagement()` 커스텀 훅 생성 |
| 에러 핸들링 패턴 | ⚠️ 개선 필요 | 20+ 파일 | 동일한 catch 블록 반복 | `formatErrorMessage()` 유틸리티 함수 |
| 데이터 fetch 패턴 | ⚠️ 개선 필요 | 8+ 페이지 | useEffect + fetch 로직 중복 | `useFetchData<T>()` 커스텀 훅 |
| 폼 유효성 검사 | ⚠️ 개선 필요 | 3개 파일 | 비슷한 검증 로직 반복 | 검증 유틸리티 함수 생성 |

### 6.2 타입 안전성

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| any 타입 사용 | ✅ 양호 | `frontend/src/*` | any 타입 사용 없음 | - |
| 타입 정의 | ✅ 양호 | `frontend/src/types/index.ts` | 192줄 포괄적 타입 정의 | - |
| 빌드 타입 체크 | ⚠️ 개선 필요 | `frontend/next.config.js:4-10` | `ignoreBuildErrors: true` 설정 | 타입 에러 수정 후 활성화 |

### 6.3 환경 분리

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| Backend 환경 설정 | ⚠️ 개선 필요 | `backend/.env` | dev/prod 값 혼재, 단일 파일 | `.env.example`, `.env.development`, `.env.production` 분리 |
| Frontend 환경 설정 | ✅ 양호 | `frontend/.env.local` | NEXT_PUBLIC_ 접두사 적절히 사용 | - |
| Docker 환경 오버라이드 | ✅ 양호 | `docker-compose.yml:48-52` | 서비스별 환경 변수 오버라이드 | - |

### 6.4 미사용 코드

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| TODO 주석 | ⚠️ 개선 필요 | `frontend/src/app/c/[campaignId]/tasks/page.tsx:129,134` | 미완성 기능 TODO 주석 | GitHub Issue로 이동 |
| 미사용 import | ✅ 양호 | - | 발견되지 않음 | - |
| 주석 처리된 코드 | ✅ 양호 | - | 발견되지 않음 | - |

---

## 7. 운영 안정성 (Operations)

### 7.1 로깅

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 로깅 설정 | 🔴 즉시 수정 | `backend/app/config.py` | 로깅 설정 없음 | 구조화된 JSON 로깅 설정 추가 |
| 요청 로깅 | 🔴 즉시 수정 | `backend/app/main.py` | 요청/응답 로깅 미들웨어 없음 | 요청 ID 포함 로깅 미들웨어 추가 |
| 에러 추적 | 🔴 즉시 수정 | - | Sentry/Datadog 등 미연동 | APM 서비스 연동 |
| 로거 사용 | ⚠️ 개선 필요 | `backend/app/services/*` | 25+ 파일 중 4개만 로깅 사용 | 주요 서비스에 로깅 추가 |

### 7.2 백업

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| DB 볼륨 설정 | ✅ 양호 | `docker-compose.yml:14,106` | Named volume 설정됨 | - |
| 백업 절차 문서화 | 🔴 즉시 수정 | - | 백업/복구 절차 문서 없음 | 백업 런북 작성 |
| Redis 영속성 | ✅ 양호 | `docker-compose.yml:28` | AOF 활성화됨 | - |
| 백업 자동화 | ⚠️ 개선 필요 | - | 자동 백업 스크립트 없음 | pg_dump 크론잡 구성 |

### 7.3 모니터링

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| 헬스 체크 엔드포인트 | ⚠️ 개선 필요 | `backend/app/main.py:87-95` | DB/Redis 연결 확인 없음 | 의존성 체크 추가 |
| Docker 헬스 체크 | ✅ 양호 | `docker-compose.yml:17-21,33-37,99-103` | PostgreSQL, Redis, MinIO 체크 | - |
| 메트릭 수집 | 🔴 즉시 수정 | - | Prometheus/메트릭 없음 | 메트릭 엔드포인트 추가 |
| 알림 설정 | 🔴 즉시 수정 | - | 서버 다운 알림 없음 | 알림 서비스 연동 |

### 7.4 배포

| 항목 | 상태 | 문제 위치 | 문제 내용 | 해결 방법 |
|------|------|-----------|-----------|-----------|
| CI/CD 파이프라인 | ✅ 양호 | `.github/workflows/test.yml` | 테스트, 린트, 타입체크 자동화 | - |
| Backend Dockerfile | ⚠️ 개선 필요 | `backend/Dockerfile:22` | dev 의존성 프로덕션에 포함 | 멀티스테이지 빌드로 변경 |
| Frontend Dockerfile | ✅ 양호 | `frontend/Dockerfile` | 멀티스테이지 빌드 적용 | - |
| Entrypoint 스크립트 | ⚠️ 개선 필요 | `backend/entrypoint.sh:17-20` | Redis 체크가 5초 sleep만 | 실제 연결 테스트로 변경 |
| 배포 문서화 | 🔴 즉시 수정 | - | 배포 절차 문서 없음 | 배포 가이드 작성 |

---

## 8. 요약

### 🔴 즉시 수정 목록 (우선순위 순)

| # | 문제 | 위치 | 심각도 |
|---|------|------|--------|
| 1 | **비밀번호 리셋 토큰 노출** | `backend/app/api/v1/auth.py:363` | CRITICAL |
| 2 | **_generate_tokens 메서드 미존재** | `backend/app/api/v1/auth.py:596,661` | CRITICAL |
| 3 | **localStorage 토큰 저장** | `frontend/src/lib/api.ts:20-42` | CRITICAL |
| 4 | **개발용 JWT 시크릿 키** | `backend/.env:30` | CRITICAL |
| 5 | **Rate Limiting 미적용** | `backend/app/main.py` | HIGH |
| 6 | **네트워크 타임아웃 미설정** | `frontend/src/lib/api.ts:66` | HIGH |
| 7 | **멤버 페이지 에러 미표시** | `frontend/src/app/c/[campaignId]/members/page.tsx:35` | HIGH |
| 8 | **영어 UI 텍스트 (멤버 페이지)** | `frontend/src/app/c/[campaignId]/members/page.tsx` | HIGH |
| 9 | **영어 UI 텍스트 (결재 페이지)** | `frontend/src/app/c/[campaignId]/approvals/page.tsx` | HIGH |
| 10 | **결재 목록 N+1 쿼리** | `backend/app/services/approval_service.py:390-425` | HIGH |
| 11 | **React.memo 미사용** | `frontend/src/components/*` | HIGH |
| 12 | **useMemo 미사용 (대시보드)** | `frontend/src/app/c/[campaignId]/dashboard/page.tsx:88-97` | HIGH |
| 13 | **로깅 시스템 미구현** | `backend/app/*` | HIGH |
| 14 | **모니터링/알림 없음** | - | HIGH |
| 15 | **백업 절차 미문서화** | - | HIGH |

### ⚠️ 개선 권고 목록

| 카테고리 | 항목 수 | 주요 내용 |
|----------|---------|-----------|
| 보안 | 8 | CSRF, OAuth 상태 관리, CORS 제한, 이메일 열거 |
| 데이터 무결성 | 4 | 초대 경쟁 조건, 자식 테이블 RLS, flush/commit 일관성 |
| 에러 처리 | 4 | 재시도 로직, Error Boundary, Validation 핸들러 |
| 성능 | 6 | 인덱스 추가, 이미지 최적화, 가상화 |
| UX/UI | 6 | 토스트 알림, 확인 다이얼로그, 테이블 반응형, 서버사이드 보호 |
| 코드 품질 | 6 | 중복 코드 제거, 커스텀 훅 생성, 환경 분리 |
| 운영 | 4 | 헬스 체크 강화, Dockerfile 최적화, entrypoint 개선 |

### ✅ 양호 항목 요약

| 카테고리 | 양호 항목 |
|----------|-----------|
| 보안 | JWT 토큰 만료, Superadmin 보호, SQL Injection 방어, 초대 토큰 보안, Origin 제한 |
| 데이터 무결성 | 트랜잭션 자동 관리, 외래키 제약, 유니크 제약, 메인 테이블 RLS |
| 에러 처리 | 전역 예외 핸들러, 서비스 예외 클래스, 로딩/에러/빈 상태 컴포넌트 |
| 성능 | 페이지네이션 구현, 주요 인덱스 설정 |
| UX/UI | 사이드바 역할 분기, 폼 유효성 검사, 반응형 그리드 |
| 코드 품질 | TypeScript any 미사용, 타입 정의 포괄적, 미사용 코드 없음 |
| 운영 | CI/CD 파이프라인, Docker 헬스 체크, Redis AOF |

---

## 다음 단계

1. **즉시 (P0)**: 🔴 목록 1-5번 보안 이슈 수정
2. **단기 (P1)**: 🔴 목록 6-15번 수정, 영어 텍스트 한국어화
3. **중기 (P2)**: ⚠️ 개선 권고 항목 순차 적용
4. **장기**: 모니터링 인프라 구축, 성능 최적화

---

*이 문서는 Claude (Opus 4.5)에 의해 자동 생성되었습니다.*
*수정 작업은 사용자 승인 후 진행됩니다.*
