# CampBoard (캠프보드) - Claude 세션 가이드

> **새 세션 시작 시 반드시 이 파일과 `docs/progress.md`를 먼저 읽을 것**

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트 이름** | 캠프보드 (CampBoard) |
| **도메인** | `election.bestcome.org` |
| **목적** | 선거 캠페인 운영 관리 시스템 (작업/일정/결재/팀원 관리) |

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **프론트엔드** | Next.js 14 (App Router) + TypeScript + shadcn-ui + Tailwind CSS |
| **백엔드** | FastAPI (Python 3.12) + SQLAlchemy 2.0 (async) |
| **데이터베이스** | PostgreSQL 16 |
| **캐시/세션** | Redis |
| **파일 스토리지** | MinIO (S3 호환) |
| **인프라** | Docker Compose, Cloudflare (DNS) |

---

## 디렉토리 구조

```
/var/www/election/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 라우터
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── schemas/         # Pydantic 스키마
│   │   ├── services/        # 비즈니스 로직
│   │   └── core/            # 보안, 설정
│   ├── alembic/             # DB 마이그레이션
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React 컴포넌트
│   │   │   ├── ui/          # shadcn/ui 기반
│   │   │   ├── common/      # 공통 컴포넌트
│   │   │   ├── dashboard/   # 대시보드 위젯
│   │   │   ├── tasks/       # 작업 관리
│   │   │   └── calendar/    # 캘린더
│   │   └── lib/             # 유틸리티
│   └── docs/
├── docs/                    # 프로젝트 문서
├── docker-compose.yml
└── CLAUDE.md               # (이 파일)
```

---

## 현재 구현 상태 (2026-03-20)

### 완료됨
- 인증: 이메일/비밀번호 로그인, JWT, 토큰 갱신, 로그아웃
- Google OAuth: 기존 사용자 로그인
- 초대 시스템: 이메일 기반 초대 및 회원가입
- RBAC: 역할(Owner/Admin/DepartmentHead/Member/Volunteer) 및 25+ 권한
- 작업 관리: 칸반 보드, CRUD, 담당자, 댓글, 히스토리
- 캘린더: 일정 조회 (Google Calendar 연동 준비)
- 결재: 결재 요청/승인/거부 워크플로우
- 팀원 관리: 멤버십, 부서, 역할 관리
- UI: 로그인, 대시보드, 작업보드, 캘린더, 멤버 페이지

### 미완성
- ~~Google OAuth로 초대된 이메일 자동 회원가입~~ ✅ 완료
- ~~부서별 권한 필터링~~ ✅ 완료
- 비밀번호 변경 UI (🟡 Medium)
- 접근성/반응형 QA (🟡 Low)

---

## 핵심 규칙

### 1. 기존 기획과 구조 유지
- 이미 설계된 DB 스키마, API 구조, UI 레이아웃을 존중
- 큰 변경이 필요하면 **반드시 먼저 승인 요청**

### 2. 코드 수정 전 설명
- 무엇을 왜 바꾸는지 먼저 설명
- 영향 받는 파일 목록 제시

### 3. UI 텍스트 규칙
- 모든 사용자 대면 텍스트는 **한국어**
- 간결하고 명확하게 (예: "저장했습니다" ✓, "성공적으로 저장되었습니다" ✗)

### 4. 세션 시작 시 항상
1. `CLAUDE.md` 읽기 (이 파일)
2. `docs/progress.md` 읽기
3. 현재 상태 파악 후 작업 시작

---

## 주요 문서

| 파일 | 설명 |
|------|------|
| `docs/progress.md` | 진행 상황 및 TODO |
| `docs/auth-rbac.md` | 인증/인가 시스템 상세 |
| `docs/uiux-plan.md` | UI/UX 설계 및 컴포넌트 |
| `frontend/DESIGN_SYSTEM.md` | 디자인 토큰 및 가이드 |
| `CRITICAL_REVIEW.md` | 코드 리뷰 결과 (참고용) |

---

## 다음 할 일 (우선순위 순)

### ✅ Critical (완료됨)
1. ~~**Google OAuth 초대 이메일 자동 회원가입**~~ ✅
2. ~~**부서별 권한 필터링 적용**~~ ✅

### 🟡 Medium (다음 작업)
3. **비밀번호 변경 UI 연결**
   - 백엔드 완료: `POST /auth/password/change`
   - 프론트엔드 페이지 생성 필요

4. **RLS(Row-Level Security) 정책 추가**
   - PostgreSQL RLS로 테넌트 격리 강화

### 🟢 Low
5. UI/UX QA (접근성, 반응형)
6. 초대 재발송 API
7. 프론트엔드 권한별 UI 분기

---

## 환경 변수 확인

### Backend (`backend/.env`)
```env
API_BASE_URL=https://election.bestcome.org
FRONTEND_BASE_URL=https://election.bestcome.org
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET_KEY=<변경 필요>
GOOGLE_OAUTH_CLIENT_ID=<설정 필요>
GOOGLE_OAUTH_CLIENT_SECRET=<설정 필요>
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=https://election.bestcome.org/api/v1
NEXT_PUBLIC_SITE_URL=https://election.bestcome.org
```

---

*마지막 업데이트: 2026-03-20*
