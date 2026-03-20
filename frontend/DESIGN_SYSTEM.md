# Campaign OS Design System

교육감 선거 캠페인을 위한 디자인 시스템

---

## Design Direction Proposals

### Direction 1: 서울교육 실용주의 (Pragmatic Education)

**철학:** 실질적인 변화, 측정 가능한 성과, 신뢰할 수 있는 리더십
**키워드:** 신뢰, 안정, 전문성, 체계

**Color Palette:**
| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary | Navy Blue | `#1e3a5f` | Headers, primary actions, trust |
| Secondary | Steel Blue | `#4a6fa5` | Secondary buttons, links |
| Accent | Gold | `#c9a227` | Highlights, achievements, CTAs |
| Success | Forest Green | `#2d6a4f` | Completed, approved |
| Warning | Amber | `#d4a017` | Pending, attention needed |
| Danger | Crimson | `#9b2335` | Errors, critical |
| Background | Warm White | `#fafaf8` | Page background |
| Surface | Pure White | `#ffffff` | Cards, modals |
| Border | Cool Gray | `#d1d5db` | Dividers, borders |
| Text Primary | Charcoal | `#1f2937` | Headings, body |
| Text Secondary | Slate | `#6b7280` | Captions, metadata |

**Typography:**
- Display: Pretendard Bold, 48px — 캠페인 슬로건
- H1: Pretendard SemiBold, 32px — 페이지 제목
- H2: Pretendard SemiBold, 24px — 섹션 제목
- H3: Pretendard Medium, 20px — 카드 제목
- Body: Pretendard Regular, 16px — 본문
- Caption: Pretendard Regular, 14px — 메타데이터

**Iconography:** Outlined, 1.5px stroke, rounded corners. 공공기관 느낌의 정돈된 아이콘.

---

### Direction 2: 현장 중심 교육 (Field-Centered Education)

**철학:** 학교 현장의 목소리, 교사·학생·학부모 중심, 따뜻한 공동체
**키워드:** 소통, 공감, 현장, 연대

**Color Palette:**
| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary | Warm Teal | `#0d9488` | Primary actions, connection |
| Secondary | Soft Teal | `#5eead4` | Highlights, tags |
| Accent | Coral | `#f97316` | CTAs, important notices |
| Success | Mint | `#34d399` | Positive outcomes |
| Warning | Sunflower | `#fbbf24` | Attention needed |
| Danger | Rose | `#fb7185` | Errors, urgent |
| Background | Cream | `#fefce8` | Warm, welcoming base |
| Surface | White | `#ffffff` | Cards |
| Border | Warm Gray | `#e5e5e5` | Soft dividers |
| Text Primary | Warm Black | `#292524` | Readable, friendly |
| Text Secondary | Stone | `#78716c` | Supporting text |

**Typography:**
- Display: Noto Sans KR Bold, 44px — 감성적 슬로건
- H1: Noto Sans KR Bold, 30px — 페이지 제목
- H2: Noto Sans KR Medium, 22px — 섹션 제목
- H3: Noto Sans KR Medium, 18px — 카드 제목
- Body: Noto Sans KR Regular, 16px — 본문
- Caption: Noto Sans KR Regular, 14px — 부가 정보

**Iconography:** Filled with soft edges, friendly and approachable. 손그림 느낌의 따뜻한 아이콘.

---

### Direction 3: AI 시대 교육 (Education for the AI Era) ✅ SELECTED

**철학:** 미래 지향, 혁신적 교육, 디지털 전환, 글로벌 경쟁력
**키워드:** 혁신, 미래, 기술, 가능성

**Color Palette:**
| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary | Electric Indigo | `#6366f1` | Primary actions, innovation |
| Secondary | Violet | `#8b5cf6` | Secondary elements, gradients |
| Accent | Cyan | `#06b6d4` | Highlights, links, tech feel |
| Success | Emerald | `#10b981` | Completed, approved, positive |
| Warning | Amber | `#f59e0b` | Pending, attention |
| Danger | Rose | `#f43f5e` | Errors, critical, overdue |
| Info | Sky | `#0ea5e9` | Information, tips |
| Background | Slate 50 | `#f8fafc` | Clean, modern base |
| Surface | White | `#ffffff` | Cards, elevated surfaces |
| Surface Elevated | Slate 100 | `#f1f5f9` | Nested cards, hover states |
| Border | Slate 200 | `#e2e8f0` | Subtle dividers |
| Border Strong | Slate 300 | `#cbd5e1` | Emphasized borders |
| Text Primary | Slate 900 | `#0f172a` | Headings, important text |
| Text Secondary | Slate 500 | `#64748b` | Body text, descriptions |
| Text Muted | Slate 400 | `#94a3b8` | Placeholders, disabled |

---

## Selected Direction: AI 시대 교육

### Design Philosophy

> "미래를 준비하는 교육, 혁신을 이끄는 리더십"

이 디자인 시스템은 AI 시대의 교육 비전을 반영합니다:
- **혁신적:** 현대적이고 세련된 인터페이스
- **효율적:** 명확한 정보 계층과 빠른 의사결정 지원
- **신뢰성:** 전문적이면서도 접근 가능한 디자인
- **미래지향:** 기술 친화적이고 확장 가능한 시스템

---

## Color System

### Primary Colors

```css
--color-primary-50: #eef2ff;
--color-primary-100: #e0e7ff;
--color-primary-200: #c7d2fe;
--color-primary-300: #a5b4fc;
--color-primary-400: #818cf8;
--color-primary-500: #6366f1;  /* Main Primary */
--color-primary-600: #4f46e5;
--color-primary-700: #4338ca;
--color-primary-800: #3730a3;
--color-primary-900: #312e81;
--color-primary-950: #1e1b4b;
```

### Secondary Colors (Violet)

```css
--color-secondary-50: #f5f3ff;
--color-secondary-100: #ede9fe;
--color-secondary-200: #ddd6fe;
--color-secondary-300: #c4b5fd;
--color-secondary-400: #a78bfa;
--color-secondary-500: #8b5cf6;  /* Main Secondary */
--color-secondary-600: #7c3aed;
--color-secondary-700: #6d28d9;
--color-secondary-800: #5b21b6;
--color-secondary-900: #4c1d95;
```

### Accent Colors (Cyan)

```css
--color-accent-50: #ecfeff;
--color-accent-100: #cffafe;
--color-accent-200: #a5f3fc;
--color-accent-300: #67e8f9;
--color-accent-400: #22d3ee;
--color-accent-500: #06b6d4;  /* Main Accent */
--color-accent-600: #0891b2;
--color-accent-700: #0e7490;
--color-accent-800: #155e75;
--color-accent-900: #164e63;
```

### Semantic Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `success` | `#10b981` | `#34d399` | 완료, 승인, 긍정적 상태 |
| `warning` | `#f59e0b` | `#fbbf24` | 주의, 대기중, 마감 임박 |
| `danger` | `#f43f5e` | `#fb7185` | 오류, 거부, 긴급 |
| `info` | `#0ea5e9` | `#38bdf8` | 정보, 도움말, 팁 |

### Background & Surface

| Token | Value | Usage |
|-------|-------|-------|
| `bg-base` | `#f8fafc` | 페이지 배경 |
| `bg-surface` | `#ffffff` | 카드, 모달, 팝오버 |
| `bg-surface-elevated` | `#f1f5f9` | 호버 상태, 중첩 카드 |
| `bg-surface-sunken` | `#e2e8f0` | 입력 필드 배경 |

### Border Colors

| Token | Value | Usage |
|-------|-------|-------|
| `border-subtle` | `#e2e8f0` | 기본 구분선 |
| `border-default` | `#cbd5e1` | 카드 테두리 |
| `border-strong` | `#94a3b8` | 강조 테두리 |
| `border-focus` | `#6366f1` | 포커스 링 |

### Text Colors

| Token | Value | Usage |
|-------|-------|-------|
| `text-primary` | `#0f172a` | 제목, 중요 텍스트 |
| `text-secondary` | `#475569` | 본문, 설명 |
| `text-tertiary` | `#64748b` | 부가 정보 |
| `text-muted` | `#94a3b8` | 플레이스홀더, 비활성 |
| `text-inverse` | `#ffffff` | 어두운 배경 위 텍스트 |

---

## Typography

### Font Family

```css
--font-sans: 'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont,
             'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
```

### Type Scale

| Name | Size | Line Height | Weight | Usage |
|------|------|-------------|--------|-------|
| `display` | 48px / 3rem | 1.1 | 700 | 캠페인 슬로건, 히어로 섹션 |
| `h1` | 36px / 2.25rem | 1.2 | 600 | 페이지 제목 |
| `h2` | 28px / 1.75rem | 1.25 | 600 | 섹션 제목 |
| `h3` | 22px / 1.375rem | 1.3 | 600 | 카드 제목, 서브섹션 |
| `h4` | 18px / 1.125rem | 1.4 | 600 | 작은 제목 |
| `body-lg` | 18px / 1.125rem | 1.6 | 400 | 강조 본문 |
| `body` | 16px / 1rem | 1.6 | 400 | 기본 본문 |
| `body-sm` | 14px / 0.875rem | 1.5 | 400 | 보조 텍스트 |
| `caption` | 12px / 0.75rem | 1.4 | 400 | 메타데이터, 타임스탬프 |
| `overline` | 12px / 0.75rem | 1.4 | 600 | 라벨, 카테고리 (uppercase) |

### Typography Rules

1. **제목 (Headings)**
   - 항상 `text-primary` 색상 사용
   - h1, h2는 페이지당 1개씩만 사용
   - 제목 간 최소 8px 간격

2. **본문 (Body)**
   - 기본 `text-secondary` 색상
   - 최대 너비 65-75 characters (가독성)
   - 문단 간격 1.5em

3. **강조 (Emphasis)**
   - Bold: 중요 키워드
   - Primary color: 액션 가능한 링크
   - Accent color: 하이라이트

---

## Iconography

### Icon Style

- **Library:** Lucide Icons
- **Style:** Outlined, 1.5px stroke weight
- **Corners:** Rounded (2px radius)
- **Sizing:**
  - Small: 16px (인라인, 버튼)
  - Medium: 20px (목록, 네비게이션)
  - Large: 24px (카드 아이콘, 빈 상태)
  - XLarge: 32px+ (히어로, 기능 소개)

### Icon Usage Guidelines

| Context | Icon Style | Color |
|---------|------------|-------|
| Navigation | Outlined, medium | `text-secondary` → `text-primary` on active |
| Buttons | Outlined, small | Inherit from button |
| Status indicators | Filled or outlined | Semantic color (success/warning/danger) |
| Empty states | Outlined, xlarge | `text-muted` |
| Decorative | Outlined, any size | `text-tertiary` or accent |

### Icon Pairing Rules

1. **텍스트와 함께:** 아이콘 오른쪽에 4-8px 간격
2. **버튼 내부:** 텍스트 왼쪽, 8px 간격
3. **단독 사용:** 툴팁 필수 (접근성)
4. **상태 표시:** 색상으로 의미 전달 + 아이콘 모양으로 보조

### Common Icons

| Action | Icon | Usage |
|--------|------|-------|
| Dashboard | `LayoutDashboard` | 대시보드 네비게이션 |
| Tasks | `CheckSquare` | 작업 관리 |
| Calendar | `Calendar` | 일정 |
| Team | `Users` | 팀원 |
| Approvals | `ClipboardCheck` | 승인 |
| Add | `Plus` | 새로 만들기 |
| Edit | `Pencil` | 수정 |
| Delete | `Trash2` | 삭제 |
| Search | `Search` | 검색 |
| Filter | `SlidersHorizontal` | 필터 |
| More | `MoreHorizontal` | 추가 옵션 |
| Close | `X` | 닫기 |
| Back | `ArrowLeft` | 뒤로 |
| Success | `CheckCircle` | 성공 상태 |
| Warning | `AlertTriangle` | 경고 상태 |
| Error | `XCircle` | 오류 상태 |
| Info | `Info` | 정보 |

---

## Spacing System

8px 기반 스페이싱 시스템

| Token | Value | Usage |
|-------|-------|-------|
| `space-0` | 0 | - |
| `space-1` | 4px | 아이콘-텍스트 간격 |
| `space-2` | 8px | 작은 요소 간격 |
| `space-3` | 12px | 관련 요소 그룹 |
| `space-4` | 16px | 기본 패딩 |
| `space-5` | 20px | 섹션 내부 |
| `space-6` | 24px | 카드 패딩 |
| `space-8` | 32px | 섹션 간격 |
| `space-10` | 40px | 큰 섹션 간격 |
| `space-12` | 48px | 페이지 섹션 |
| `space-16` | 64px | 페이지 상단/하단 |

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-none` | 0 | - |
| `rounded-sm` | 4px | 작은 요소 (태그, 뱃지) |
| `rounded` | 6px | 버튼, 입력 필드 |
| `rounded-md` | 8px | 카드, 드롭다운 |
| `rounded-lg` | 12px | 모달, 큰 카드 |
| `rounded-xl` | 16px | 히어로 카드 |
| `rounded-full` | 9999px | 아바타, 원형 버튼 |

---

## Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)` | 미묘한 분리 |
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.1)` | 카드 기본 |
| `shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | 드롭다운, 호버 |
| `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | 모달 |
| `shadow-xl` | `0 20px 25px rgba(0,0,0,0.1)` | 플로팅 요소 |
| `shadow-inner` | `inset 0 2px 4px rgba(0,0,0,0.05)` | 눌린 상태 |

---

## Animation

### Timing Functions

```css
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
```

### Duration

| Token | Value | Usage |
|-------|-------|-------|
| `duration-fast` | 100ms | 호버 상태 |
| `duration-normal` | 200ms | 일반 전환 |
| `duration-slow` | 300ms | 페이지 전환, 모달 |
| `duration-slower` | 500ms | 복잡한 애니메이션 |

### Motion Patterns

1. **Fade In Up** - 페이지 로드, 카드 등장
   ```
   opacity: 0 → 1
   translateY: 10px → 0
   duration: 300ms
   ```

2. **Scale In** - 모달, 드롭다운 등장
   ```
   opacity: 0 → 1
   scale: 0.95 → 1
   duration: 200ms
   ```

3. **Slide In** - 사이드바, 패널
   ```
   translateX: -100% → 0
   duration: 300ms
   ```

4. **Stagger** - 목록 아이템
   ```
   각 아이템 50ms 딜레이
   Fade In Up 적용
   ```

---

## Component Tokens

### Button

| Variant | Background | Text | Border | Hover |
|---------|------------|------|--------|-------|
| Primary | `primary-500` | white | none | `primary-600` |
| Secondary | white | `primary-600` | `primary-200` | `primary-50` |
| Ghost | transparent | `text-secondary` | none | `slate-100` |
| Danger | `danger` | white | none | darker 10% |

### Input

| State | Border | Background | Ring |
|-------|--------|------------|------|
| Default | `border-default` | white | none |
| Focus | `primary-500` | white | `primary-100` 3px |
| Error | `danger` | `rose-50` | `rose-100` 3px |
| Disabled | `border-subtle` | `slate-50` | none |

### Card

| Variant | Background | Border | Shadow |
|---------|------------|--------|--------|
| Default | white | `border-subtle` | `shadow-sm` |
| Elevated | white | none | `shadow-md` |
| Interactive | white | `border-subtle` | `shadow-sm` → `shadow-md` on hover |

### Badge

| Variant | Background | Text |
|---------|------------|------|
| Default | `slate-100` | `slate-700` |
| Primary | `primary-100` | `primary-700` |
| Success | `emerald-100` | `emerald-700` |
| Warning | `amber-100` | `amber-700` |
| Danger | `rose-100` | `rose-700` |
| Info | `sky-100` | `sky-700` |

---

## Page Layouts

### Login Page
- 중앙 정렬 카드 (max-width: 400px)
- 그라데이션 배경 (primary-500 → secondary-500, 15도 각도)
- 로고 + 슬로건 상단
- 폼 + 소셜 로그인 옵션

### Dashboard
- 사이드바 (240px) + 메인 콘텐츠
- 상단: 환영 메시지 + Quick Actions
- 통계 카드 그리드 (4열)
- 최근 활동 섹션 (2열: 작업 + 일정)

### List Pages (Tasks, Members, Approvals)
- 상단 툴바: 검색 + 필터 + 액션 버튼
- 뷰 토글 (그리드/리스트)
- 페이지네이션 하단

### Detail Pages
- 브레드크럼 네비게이션
- 상단: 제목 + 상태 + 액션
- 2열 레이아웃: 메인 콘텐츠 (2/3) + 사이드바 (1/3)

---

## Accessibility

### Color Contrast
- 모든 텍스트 WCAG AA 준수 (4.5:1 이상)
- 대형 텍스트 (18px+) 3:1 이상

### Focus States
- 모든 인터랙티브 요소에 visible focus ring
- `outline: 2px solid primary-500`
- `outline-offset: 2px`

### Motion
- `prefers-reduced-motion` 지원
- 필수 애니메이션만 유지 (감소 모드)

---

## File Structure

```
src/
├── styles/
│   └── design-tokens.css     # CSS 변수 정의
├── components/
│   └── ui/                   # shadcn/ui 기반 컴포넌트
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── badge.tsx
│       └── ...
├── lib/
│   └── utils.ts              # cn() 헬퍼, 유틸리티
└── app/
    └── globals.css           # 글로벌 스타일, 토큰 import
```

---

*Last updated: 2024-01*
*Design System Version: 1.0*
