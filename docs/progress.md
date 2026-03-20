# 프로젝트 진행 상황

캠프보드 (CampBoard) 개발 진행 상황 추적 문서

> **마지막 업데이트:** 2026-03-20 (프론트엔드 UI 개선 완료)

---

## ✅ 완료된 작업

### 인프라 & 설정
- [x] Docker Compose 구성 (PostgreSQL, Redis, MinIO, Backend, Frontend)
- [x] 환경변수 설정 (`election.bestcome.org` 기준)
- [x] Alembic 마이그레이션 설정
- [x] GitHub Actions CI/CD 기본 구성

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
- [x] 작업 관리 API (CRUD, 이동, 담당자, 댓글, 히스토리)
- [x] 결재 워크플로우 API
- [x] 페이지네이션 지원

### 프론트엔드 (Next.js)
- [x] 디자인 시스템 문서화 (`DESIGN_SYSTEM.md`)
- [x] shadcn/ui 기반 컴포넌트 20+개
- [x] 로그인 페이지 (이메일 + Google OAuth)
- [x] OAuth 콜백 처리
- [x] 초대 수락 페이지
- [x] 대시보드 레이아웃 (사이드바 + 헤더)
- [x] 캠페인 목록 페이지
- [x] 대시보드 위젯 컴포넌트
- [x] 작업 보드 (칸반 + 리스트 뷰)
- [x] 캘린더 페이지
- [x] 멤버 목록 페이지
- [x] 결재 목록 페이지
- [x] 비밀번호 변경 페이지 (`/settings`)
- [x] 메인 랜딩 페이지 개선 (Google 로그인 CTA)
- [x] 초대 수락 페이지 개선 (상태별 UI, Google 가입 옵션)

---

## 🟡 진행 중인 작업

### 현재 세션 (2026-03-20)
- [ ] 크리티컬 리뷰 결과 문서화 ✅ 완료
- [ ] MD 파일 생성 (CLAUDE.md, auth-rbac.md, uiux-plan.md, progress.md) ✅ 완료

---

## 🔴 미착수 작업 (TODO)

### 🔴 Critical (즉시 필요)

#### ~~1. Google OAuth 초대 이메일 자동 회원가입~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `backend/app/api/v1/auth.py:605-668`

#### ~~2. 부서별 권한 필터링 적용~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `backend/app/services/task_service.py:83-130, 276-389`
- **구현 내용:**
  - `list_boards()`: 권한별 보드 필터링
  - `list_tasks()`: 권한별 작업 필터링
  - TASK_VIEW_ALL → 전체 조회
  - TASK_VIEW_DEPARTMENT → 자기 부서 + 할당된 작업
  - 권한 없음 → 할당된 작업만

#### ~~3. 비밀번호 변경 UI~~ ✅ 완료
- **완료일:** 2026-03-20
- **위치:** `frontend/src/app/settings/page.tsx`
- **구현 내용:**
  - `/settings` 페이지 생성
  - 현재 비밀번호 + 새 비밀번호 + 확인 입력 폼
  - 비밀번호 표시/숨김 토글
  - 유효성 검증 및 에러/성공 상태 표시
  - `api.post('/auth/password/change')` 연동

### 🟡 Medium (곧 필요)

#### 4. PostgreSQL RLS(Row-Level Security) 정책
- **위치:** `backend/alembic/versions/` (새 마이그레이션 필요)
- **현황:** `set_tenant_context()` 함수는 있으나 실제 RLS 정책 없음
- **필요 작업:**
  ```sql
  ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
  CREATE POLICY tenant_isolation_tasks ON tasks
    USING (campaign_id = current_setting('app.current_campaign_id')::int);
  ```

#### 5. 토큰 저장소 보안 강화
- **현황:** localStorage에 토큰 저장 (XSS 취약)
- **권장:** httpOnly 쿠키 또는 메모리 저장 + refresh token rotation

### 🟢 Low (나중에)

#### 6. UI/UX QA
- 접근성 테스트 (키보드, 스크린 리더)
- 반응형 테스트 (태블릿, 모바일)
- 색상 대비 WCAG AA 검증

#### 7. 초대 재발송 API
- 현재: 새 초대 생성으로 대체 가능
- 개선: 기존 초대 토큰 재발송 기능

#### 8. 프론트엔드 권한별 UI 분기
- 역할에 따라 메뉴/버튼 표시/숨김
- 권한 없는 페이지 접근 시 리다이렉트

#### 9. 알림 시스템
- 실시간 알림 (WebSocket)
- 이메일 알림 연동

#### 10. 파일 업로드 검증
- MIME 타입 검증
- 파일 크기 제한 적용

---

## ⚠️ 크리티컬 리스크 목록

| # | 리스크 | 심각도 | 위치 | 대응 |
|---|--------|--------|------|------|
| 1 | RLS 정책 미적용 | HIGH | DB 전체 | 마이그레이션 추가 |
| 2 | 개발용 시크릿 키 | HIGH | `backend/.env` | 프로덕션 배포 전 변경 |
| ~~3~~ | ~~부서 권한 미적용~~ | ~~HIGH~~ | ~~task_service.py~~ | ✅ 완료 |
| 4 | localStorage 토큰 | MEDIUM | api.ts | httpOnly 쿠키 전환 |
| 5 | 비밀번호 리셋 토큰 노출 | HIGH | auth.py:361 | debug_token 제거 |
| 6 | Redis 인증 없음 | MEDIUM | docker-compose.yml | 비밀번호 설정 |
| 7 | CORS 전체 허용 | MEDIUM | main.py | 허용 메서드/헤더 제한 |

---

## 📊 진행률 요약

| 영역 | 완료 | 진행중 | 미착수 | 진행률 |
|------|------|--------|--------|--------|
| 인프라 | 4 | 0 | 2 | 67% |
| 백엔드 API | 8 | 0 | 3 | 73% |
| 프론트엔드 | 15 | 0 | 2 | 88% |
| 보안 | 2 | 0 | 5 | 29% |
| **전체** | **29** | **0** | **12** | **71%** |

---

## 📅 마일스톤

### M1: MVP (현재)
- [x] 인증 시스템
- [x] 작업 관리
- [x] 팀원 관리
- [x] Google OAuth 초대 회원가입
- [x] 부서 권한 필터링

### M2: 베타
- [ ] RLS 보안 적용
- [x] 비밀번호 변경 UI
- [ ] 알림 시스템
- [ ] 파일 업로드

### M3: 정식 출시
- [ ] 프로덕션 보안 설정
- [ ] 성능 최적화
- [ ] 모니터링/로깅

---

*새 세션 시작 시 이 파일과 `CLAUDE.md`를 먼저 읽어주세요.*
