# UI/UX 설계 및 계획

캠프보드 프론트엔드 UI/UX 시스템 문서

---

## 1. 디자인 시스템 개요

### 1.1 선택된 방향: AI 시대 교육

**철학:** 미래 지향, 혁신적 교육, 디지털 전환
**키워드:** 혁신, 미래, 기술, 가능성

### 1.2 핵심 컬러

| 역할 | 색상 | Hex | 용도 |
|------|------|-----|------|
| Primary | Electric Indigo | `#6366f1` | 주요 액션, 브랜드 |
| Secondary | Violet | `#8b5cf6` | 보조 요소, 그라데이션 |
| Accent | Cyan | `#06b6d4` | 하이라이트, 링크 |
| Success | Emerald | `#10b981` | 완료, 승인 |
| Warning | Amber | `#f59e0b` | 주의, 대기 |
| Danger | Rose | `#f43f5e` | 오류, 긴급 |

### 1.3 타이포그래피

- **폰트:** Pretendard Variable
- **제목:** SemiBold/Bold, 22-36px
- **본문:** Regular, 14-16px
- **캡션:** Regular, 12px

상세 내용: `frontend/DESIGN_SYSTEM.md` 참조

---

## 2. UI 업그레이드 완료 항목

### 2.1 레이아웃

- [x] **GlobalHeader** - 상단 네비게이션, 사용자 메뉴
- [x] **Sidebar** - 접을 수 있는 사이드바, 네비게이션 메뉴
- [x] **DashboardLayout** - 메인 레이아웃 래퍼

### 2.2 페이지

- [x] **로그인 페이지** (`/login`) - 이메일/비밀번호 + Google OAuth
- [x] **초대 수락 페이지** (`/invite/[token]`) - 회원가입 폼
- [x] **OAuth 콜백** (`/login/callback`) - 토큰 처리
- [x] **캠페인 목록** (`/campaigns`) - 내 캠페인 리스트
- [x] **대시보드** (`/c/[id]/dashboard`) - 역할별 위젯
- [x] **작업 보드** (`/c/[id]/tasks`) - 칸반 + 리스트 뷰
- [x] **캘린더** (`/c/[id]/calendar`) - 월간/주간/리스트 뷰
- [x] **멤버** (`/c/[id]/members`) - 팀원 목록
- [x] **결재** (`/c/[id]/approvals`) - 결재 요청 목록

### 2.3 기능 컴포넌트

- [x] **TaskCard** - 작업 카드 (칸반용)
- [x] **TaskColumn** - 칸반 컬럼
- [x] **TaskBoard** - 칸반 보드 전체
- [x] **TaskListView** - 리스트 뷰
- [x] **TaskFilters** - 필터 UI
- [x] **CalendarGrid** - 캘린더 그리드
- [x] **EventDetailPanel** - 일정 상세 패널

---

## 3. shadcn/ui 기반 컴포넌트 목록

### 3.1 기본 UI (`frontend/src/components/ui/`)

| 컴포넌트 | 파일 | 상태 |
|----------|------|------|
| Button | `button.tsx` | ✅ |
| Card | `card.tsx` | ✅ |
| Input | `input.tsx` | ✅ |
| Badge | `badge.tsx` | ✅ |
| Avatar | `avatar.tsx` | ✅ |
| Table | `table.tsx` | ✅ |
| Dialog | `dialog.tsx` | ✅ |
| Sheet | `sheet.tsx` | ✅ |
| Dropdown Menu | `dropdown-menu.tsx` | ✅ |
| Select | `select.tsx` | ✅ |
| Checkbox | `checkbox.tsx` | ✅ |
| Tabs | `tabs.tsx` | ✅ |
| Toggle | `toggle.tsx` | ✅ |
| Toggle Group | `toggle-group.tsx` | ✅ |
| Tooltip | `tooltip.tsx` | ✅ |
| Popover | `popover.tsx` | ✅ |
| Progress | `progress.tsx` | ✅ |
| Skeleton | `skeleton.tsx` | ✅ |
| Alert | `alert.tsx` | ✅ |
| Separator | `separator.tsx` | ✅ |
| Collapsible | `collapsible.tsx` | ✅ |

### 3.2 공통 컴포넌트 (`frontend/src/components/common/`)

| 컴포넌트 | 파일 | 용도 |
|----------|------|------|
| UserAvatar | `UserAvatar.tsx` | 사용자 아바타 |
| UserAvatarGroup | `UserAvatarGroup.tsx` | 아바타 그룹 |
| StatusBadge | `StatusBadge.tsx` | 상태 뱃지 |
| PriorityBadge | `PriorityBadge.tsx` | 우선순위 뱃지 |
| DueDateDisplay | `DueDateDisplay.tsx` | 마감일 표시 |
| EmptyState | `EmptyState.tsx` | 빈 상태 UI |
| ErrorState | `ErrorState.tsx` | 에러 상태 UI |
| LoadingState | `LoadingState.tsx` | 로딩 상태 UI |

### 3.3 대시보드 위젯 (`frontend/src/components/dashboard/`)

| 컴포넌트 | 파일 | 용도 |
|----------|------|------|
| AlertBanner | `AlertBanner.tsx` | 알림 배너 |
| MyTasksWidget | `MyTasksWidget.tsx` | 내 작업 위젯 |
| TodayScheduleWidget | `TodayScheduleWidget.tsx` | 오늘 일정 |
| PendingApprovalsWidget | `PendingApprovalsWidget.tsx` | 대기 결재 |
| TeamProgressWidget | `TeamProgressWidget.tsx` | 팀 진행률 |
| AnnouncementWidget | `AnnouncementWidget.tsx` | 공지사항 |

---

## 4. 역할별 대시보드 설계

### 4.1 Owner / Admin

```
┌─────────────────────────────────────────────────────┐
│ [알림 배너: 긴급 공지 또는 중요 마감]                  │
├─────────────┬─────────────┬─────────────┬───────────┤
│ 전체 작업   │ 진행 중     │ 마감 임박    │ 완료율    │
│ 48         │ 12         │ 5          │ 73%      │
├─────────────────────────────┬───────────────────────┤
│ 내 작업 (최근 5개)          │ 오늘 일정              │
│ - [ ] 정책 검토 (D-2)       │ 10:00 팀 회의          │
│ - [ ] 보도자료 작성         │ 14:00 후보 미팅        │
│ - [ ] 예산 승인 요청        │ 16:00 홍보팀 브리핑     │
├─────────────────────────────┼───────────────────────┤
│ 대기 중인 결재 (3건)        │ 팀 진행률              │
│ - 예산 집행 요청            │ ████████░░ 정책팀 80%  │
│ - 인쇄물 발주 승인          │ ██████░░░░ 홍보팀 60%  │
└─────────────────────────────┴───────────────────────┘
```

### 4.2 Department Head

```
┌─────────────────────────────────────────────────────┐
│ [내 부서: 정책팀]                                    │
├─────────────┬─────────────┬─────────────┬───────────┤
│ 부서 작업   │ 진행 중     │ 마감 임박    │ 완료율    │
│ 15         │ 4          │ 2          │ 67%      │
├─────────────────────────────┬───────────────────────┤
│ 내 작업                     │ 팀원 현황              │
│ ...                        │ 김철수: 작업 3개       │
│                            │ 이영희: 작업 2개       │
├─────────────────────────────┼───────────────────────┤
│ 부서 결재 현황              │ 오늘 일정              │
└─────────────────────────────┴───────────────────────┘
```

### 4.3 Member / Volunteer

```
┌─────────────────────────────────────────────────────┐
│ [환영합니다, 홍길동님!]                              │
├─────────────────────────────┬───────────────────────┤
│ 내 작업                     │ 오늘 일정              │
│ - [ ] 현수막 디자인 검토     │ 14:00 디자인 회의      │
│ - [ ] SNS 콘텐츠 작성       │                       │
├─────────────────────────────┼───────────────────────┤
│ 공지사항                    │ 내 결재 요청 현황       │
│ - 이번 주 일정 변경 안내     │ 승인 대기: 1건         │
└─────────────────────────────┴───────────────────────┘
```

---

## 5. 남은 QA 항목

### 5.1 접근성 (Accessibility)

| 항목 | 상태 | 비고 |
|------|------|------|
| 키보드 네비게이션 | 🟡 미확인 | Tab 순서 검증 필요 |
| 스크린 리더 지원 | 🟡 미확인 | aria-label 추가 필요 |
| 색상 대비 | 🟡 미확인 | WCAG AA 준수 확인 |
| 포커스 표시 | ✅ | outline 스타일 적용 |

### 5.2 반응형 (Responsive)

| 뷰포트 | 상태 | 비고 |
|--------|------|------|
| Desktop (1280px+) | ✅ | 기본 레이아웃 |
| Tablet (768-1279px) | 🟡 미확인 | 사이드바 접힘 테스트 |
| Mobile (320-767px) | 🟡 미확인 | 모바일 메뉴 테스트 |

### 5.3 상태 처리

| 상태 | 구현 | 비고 |
|------|------|------|
| 로딩 | ✅ | LoadingState 컴포넌트 |
| 빈 상태 | ✅ | EmptyState 컴포넌트 |
| 오류 | ✅ | ErrorState 컴포넌트 |
| 오프라인 | ❌ | 미구현 |

### 5.4 미구현 페이지

| 페이지 | 우선순위 | 비고 |
|--------|----------|------|
| 설정 페이지 (`/settings`) | Medium | 비밀번호 변경 포함 |
| 프로필 페이지 (`/profile`) | Low | 사용자 정보 수정 |
| 알림 페이지 (`/notifications`) | Low | 알림 목록 |

---

## 6. 아이콘 시스템

**라이브러리:** Lucide Icons

### 6.1 네비게이션 아이콘

| 메뉴 | 아이콘 |
|------|--------|
| 대시보드 | `LayoutDashboard` |
| 작업 | `CheckSquare` |
| 캘린더 | `Calendar` |
| 팀원 | `Users` |
| 결재 | `ClipboardCheck` |
| 설정 | `Settings` |

### 6.2 액션 아이콘

| 액션 | 아이콘 |
|------|--------|
| 추가 | `Plus` |
| 수정 | `Pencil` |
| 삭제 | `Trash2` |
| 검색 | `Search` |
| 필터 | `SlidersHorizontal` |
| 더보기 | `MoreHorizontal` |
| 닫기 | `X` |

### 6.3 상태 아이콘

| 상태 | 아이콘 | 색상 |
|------|--------|------|
| 성공 | `CheckCircle` | `emerald-500` |
| 경고 | `AlertTriangle` | `amber-500` |
| 오류 | `XCircle` | `rose-500` |
| 정보 | `Info` | `sky-500` |

---

*마지막 업데이트: 2026-03-20*
