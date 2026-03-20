# 프로젝트 진행 상황

캠프보드 (CampBoard) 개발 진행 상황 추적 문서

> **마지막 업데이트:** 2026-03-20 (2순위 작업 완료 및 마무리 QA)

---

## ✅ 완료된 작업

### 인프라 & 설정
- [x] Docker Compose 구성 (PostgreSQL, Redis, MinIO, Backend, Frontend)
- [x] 환경변수 설정 (`election.bestcome.org` 기준)
- [x] Alembic 마이그레이션 설정
- [x] GitHub Actions CI/CD 기본 구성
- [x] Git 저장소 초기화 및 초기 커밋

### 백엔드 (FastAPI)
- [x] 데이터베이스 모델 설계 및 구현
  - User, Campaign, CampaignMembership
  - Role, Permission, Department
  - Task, TaskBoard, TaskColumn, TaskAssignment, TaskComment, TaskHistory
  - Invitation, Approval, ApprovalStep
  - GoogleCalendarConnection
- [x] JWT 인증 시스템 (access + refresh token)
- [x] 토큰 블랙리스트 (로그아웃, 세션 무효화)
- [x] Google OAuth 기존 사용자 로그인
- [x] Google OAuth 초대된 이메일 자동 회원가입
- [x] 초대 기반 회원가입 API
- [x] RBAC 권한 시스템 (25+ permissions)
- [x] 부서별 권한 필터링 (TASK_VIEW_ALL/TASK_VIEW_DEPARTMENT)
- [x] 작업 관리 API (CRUD, 이동, 담당자, 댓글, 히스토리)
- [x] 결재 워크플로우 API
- [x] 페이지네이션 지원
- [x] RLS(Row-Level Security) 마이그레이션
- [x] 역할 시드 데이터 (9개 역할: owner/admin/general_affairs/policy/communications/staff/department_head/member/volunteer)

### 프론트엔드 (Next.js)
- [x] 디자인 시스템 문서화 (`DESIGN_SYSTEM.md`)
- [x] shadcn/ui 기반 컴포넌트 20+개
- [x] 로그인 페이지 (이메일 + Google OAuth)
- [x] OAuth 콜백 처리
- [x] 초대 수락 페이지 (상태별 UI: valid/expired/already_exists/invalid)
- [x] 대시보드 레이아웃 (사이드바 + 헤더)
- [x] 캠페인 목록 페이지
- [x] 대시보드 위젯 컴포넌트
- [x] 작업 보드 (칸반 + 리스트 뷰)
- [x] 캘린더 페이지
- [x] 멤버 목록 페이지
- [x] 결재 목록 페이지
- [x] 비밀번호 변경 페이지 (`/settings`)
- [x] 메인 랜딩 페이지 (Google 로그인 CTA)
- [x] 모바일 반응형 네비게이션

### 접근성/반응형 (QA 완료)
- [x] TaskCard: 키보드 탐색, aria-label, 포커스 상태
- [x] CalendarGrid: 키보드 탐색, aria-label, aria-selected
- [x] LoadingState: role="status", aria-live
- [x] ErrorState: role="alert", aria-live
- [x] Header: 모바일 메뉴 토글 (aria-label, aria-expanded)
- [x] 반응형 브레이크포인트: 768px (md), 1024px (lg), 1280px

---

## 🟡 진행 중인 작업

현재 세션에서 모든 요청 작업이 완료되었습니다.

---

## 🔴 미착수 작업 (TODO)

### ~~🔴 Critical (즉시 필요)~~ - 모두 완료

#### ~~1. Google OAuth 초대 이메일 자동 회원가입~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `backend/app/api/v1/auth.py:605-668`

#### ~~2. 부서별 권한 필터링 적용~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `backend/app/services/task_service.py:83-130, 276-389`

#### ~~3. 비밀번호 변경 UI~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `frontend/src/app/settings/page.tsx`

#### ~~4. RLS(Row-Level Security) 정책~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `backend/alembic/versions/20240104_000000_add_row_level_security.py`

#### ~~5. 역할 시드 데이터~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `backend/app/models/role.py` (SYSTEM_ROLES)
- **역할 목록:** 캠프 대표, 관리자, 총무, 정책, 홍보, 스태프, 부서장, 팀원, 봉사자

#### ~~6. 접근성/반응형 QA~~ ✅ 완료
- **완료일:** 2026-03-20
- **수정 파일:**
  - `TaskCard.tsx`: 키보드 탐색, aria-label
  - `TaskColumn.tsx`: 버튼 aria-label
  - `CalendarGrid.tsx`: 키보드 탐색, aria-label
  - `LoadingState.tsx`: role, aria-live
  - `ErrorState.tsx`: role, aria-live
  - `Header.tsx`: 모바일 네비게이션 메뉴

### 🟢 Low (나중에)

#### 7. 토큰 저장소 보안 강화
- **현황:** localStorage에 토큰 저장 (XSS 취약)
- **권장:** httpOnly 쿠키 또는 메모리 저장 + refresh token rotation

#### 8. 초대 재발송 API
- 현재: 새 초대 생성으로 대체 가능
- 개선: 기존 초대 토큰 재발송 기능

#### 9. 프론트엔드 권한별 UI 분기
- 역할에 따라 메뉴/버튼 표시/숨김
- 권한 없는 페이지 접근 시 리다이렉트

#### 10. 알림 시스템
- 실시간 알림 (WebSocket)
- 이메일 알림 연동

#### 11. 파일 업로드 검증
- MIME 타입 검증
- 파일 크기 제한 적용

---

## ⚠️ 크리티컬 리스크 목록

| # | 리스크 | 심각도 | 위치 | 상태 |
|---|--------|--------|------|------|
| ~~1~~ | ~~RLS 정책 미적용~~ | ~~HIGH~~ | ~~DB 전체~~ | ✅ 완료 |
| 2 | 개발용 시크릿 키 | HIGH | `backend/.env` | 프로덕션 배포 전 변경 필요 |
| ~~3~~ | ~~부서 권한 미적용~~ | ~~HIGH~~ | ~~task_service.py~~ | ✅ 완료 |
| 4 | localStorage 토큰 | MEDIUM | api.ts | httpOnly 쿠키 전환 권장 |
| 5 | 비밀번호 리셋 토큰 노출 | HIGH | auth.py:361 | debug_token 제거 필요 |
| 6 | Redis 인증 없음 | MEDIUM | docker-compose.yml | 비밀번호 설정 권장 |
| 7 | CORS 전체 허용 | MEDIUM | main.py | 허용 메서드/헤더 제한 권장 |

---

## 📊 진행률 요약

| 영역 | 완료 | 진행중 | 미착수 | 진행률 |
|------|------|--------|--------|--------|
| 인프라 | 5 | 0 | 0 | 100% |
| 백엔드 API | 12 | 0 | 0 | 100% |
| 프론트엔드 | 16 | 0 | 0 | 100% |
| 보안 | 3 | 0 | 4 | 43% |
| **전체** | **36** | **0** | **4** | **90%** |

---

## 📅 마일스톤

### M1: MVP ✅ 완료
- [x] 인증 시스템
- [x] 작업 관리
- [x] 팀원 관리
- [x] Google OAuth 초대 회원가입
- [x] 부서 권한 필터링

### M2: 베타 🟡 진행중 (90% 완료)
- [x] RLS 보안 적용
- [x] 비밀번호 변경 UI
- [x] 접근성/반응형 QA
- [ ] 알림 시스템
- [ ] 파일 업로드

### M3: 정식 출시
- [ ] 프로덕션 보안 설정
- [ ] 성능 최적화
- [ ] 모니터링/로깅

---

## 📝 최종 완료 요약 (2026-03-20)

이번 세션에서 완료한 작업:

1. **RLS(Row-Level Security) 정책**: PostgreSQL RLS 마이그레이션 파일 확인 및 검증
2. **역할 시드 데이터**: 9개 역할 정의 (관리자/총무/정책/홍보/스태프 등), 한글 이름 적용
3. **접근성/반응형 QA**:
   - TaskCard: 키보드 탐색, 포커스 상태, aria-label
   - CalendarGrid: 키보드 탐색, aria-label, aria-selected
   - LoadingState/ErrorState: 스크린 리더 지원
   - Header: 모바일 네비게이션 메뉴 추가
4. **최종 동작 점검**: 사용자 흐름 확인 (로그인 → 대시보드 → 기능 → 로그아웃)
5. **Git 커밋**: 181개 파일, 38,366줄 추가

전체 프로젝트 진행률: **90%**

---

*새 세션 시작 시 이 파일과 `CLAUDE.md`를 먼저 읽어주세요.*
