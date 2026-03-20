# Micro-Interactions & Feedback System

사용자 피드백을 위한 마이크로 인터랙션 가이드

---

## Components Required

```bash
# shadcn/ui 컴포넌트 설치
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add alert
```

---

## 1. Loading States

### 1.1 Page Loading (Skeleton)

**Dashboard Page:**
```
┌─────────────────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░, ░░░░░ 👋             │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
├─────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│ │ ░░░░░░░░ │ │ ░░░░░░░░ │ │ ░░░░░░░░ │     │
│ │ ░░░░░░   │ │ ░░░░░░   │ │ ░░░░░░   │     │
│ └──────────┘ └──────────┘ └──────────┘     │
│                                             │
│ ░░░░░░░░░░                                 │
│ ┌───────────────────┐ ┌───────────────────┐│
│ │ ░░░░░░░░░░░░░░░░░ │ │ ░░░░░░░░░░░░░░░░░ ││
│ │ ░░░░░░░░░░░░░     │ │ ░░░░░░░░░░░░░     ││
│ │ ░░░░░░░░░░░░░░░░░ │ │ ░░░░░░░░░░░░░░░░░ ││
│ └───────────────────┘ └───────────────────┘│
└─────────────────────────────────────────────┘
```

**Tasks Board:**
```tsx
// TaskBoardSkeleton.tsx
<div className="flex gap-4">
  {[1, 2, 3, 4].map((col) => (
    <div key={col} className="w-72 space-y-3">
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-24 w-full rounded-lg" />
      <Skeleton className="h-24 w-full rounded-lg" />
      <Skeleton className="h-24 w-full rounded-lg" />
    </div>
  ))}
</div>
```

**Task Card Skeleton:**
```tsx
<div className="p-4 space-y-3 border rounded-lg">
  <Skeleton className="h-5 w-3/4" />
  <Skeleton className="h-4 w-1/2" />
  <div className="flex gap-2">
    <Skeleton className="h-5 w-16 rounded-full" />
    <Skeleton className="h-5 w-12 rounded-full" />
  </div>
</div>
```

**Calendar Skeleton:**
```tsx
<div className="space-y-4">
  <div className="flex justify-between items-center">
    <Skeleton className="h-8 w-32" />
    <div className="flex gap-2">
      <Skeleton className="h-8 w-8 rounded" />
      <Skeleton className="h-8 w-8 rounded" />
    </div>
  </div>
  <div className="grid grid-cols-7 gap-1">
    {Array.from({ length: 35 }).map((_, i) => (
      <Skeleton key={i} className="h-24 w-full rounded" />
    ))}
  </div>
</div>
```

### 1.2 Button Loading States

```tsx
// 버튼 로딩 상태
<Button disabled={isLoading}>
  {isLoading ? (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      처리 중...
    </>
  ) : (
    '저장하기'
  )}
</Button>
```

**로딩 텍스트 (Korean):**

| Action | Loading Text |
|--------|--------------|
| 로그인 | 로그인 중... |
| 저장 | 저장 중... |
| 생성 | 생성 중... |
| 삭제 | 삭제 중... |
| 전송 | 전송 중... |
| 불러오는 중 | 불러오는 중... |

### 1.3 Inline Loading

```tsx
// 작업 이동 시 카드 로딩
<div className={cn(
  "task-card transition-opacity",
  isMoving && "opacity-50 pointer-events-none"
)}>
  {isMoving && (
    <div className="absolute inset-0 flex items-center justify-center bg-white/50">
      <Loader2 className="h-5 w-5 animate-spin text-primary" />
    </div>
  )}
  {/* card content */}
</div>
```

---

## 2. Empty States

### 2.1 Empty State Component

```tsx
interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-slate-100 p-4 mb-4">
        <Icon className="h-8 w-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 mb-4 max-w-sm">{description}</p>
      {action && (
        <Button onClick={action.onClick}>
          <Plus className="h-4 w-4 mr-2" />
          {action.label}
        </Button>
      )}
    </div>
  );
}
```

### 2.2 Empty State Messages (Korean)

| Page/Section | Icon | Title | Description | CTA |
|--------------|------|-------|-------------|-----|
| **내 작업 없음** | `CheckCircle` | 모든 작업 완료! | 오늘 할당된 작업이 없어요 | - |
| **작업 보드 비어있음** | `ClipboardList` | 아직 작업이 없어요 | 첫 번째 작업을 만들어 보세요 | 작업 만들기 |
| **칼럼 비어있음** | `Inbox` | 이 단계에 작업이 없어요 | 작업을 드래그해서 옮겨보세요 | - |
| **일정 없음** | `Calendar` | 오늘 일정이 없어요 | 새로운 일정을 추가해 보세요 | 일정 추가 |
| **이번 달 일정 없음** | `CalendarDays` | 이번 달 일정이 없어요 | 캠페인 일정을 계획해 보세요 | 일정 추가 |
| **승인 요청 없음** | `ClipboardCheck` | 처리할 승인이 없어요 | 새로운 요청이 오면 알려드릴게요 | - |
| **팀원 없음** | `Users` | 아직 팀원이 없어요 | 함께할 팀원을 초대해 보세요 | 팀원 초대 |
| **검색 결과 없음** | `SearchX` | 검색 결과가 없어요 | 다른 키워드로 검색해 보세요 | 필터 초기화 |
| **캠페인 없음** | `Megaphone` | 참여 중인 캠페인이 없어요 | 캠페인에 참여하거나 새로 만들어 보세요 | 캠페인 만들기 |

### 2.3 Empty State Illustrations

```tsx
// 역할별 빈 상태 메시지
const roleEmptyStates = {
  'general-affairs': {
    noTasks: {
      title: '오늘 일정이 여유로워요',
      description: '내일 행사 준비를 미리 해볼까요?',
    },
  },
  'policy': {
    noTasks: {
      title: '검토할 문서가 없어요',
      description: '정책 자료를 정리해 보는 건 어떨까요?',
    },
  },
  'media': {
    noTasks: {
      title: '발행 대기 콘텐츠가 없어요',
      description: '새로운 콘텐츠 아이디어를 정리해 보세요',
    },
  },
};
```

---

## 3. Toast Notifications

### 3.1 Toast Setup

```tsx
// components/ui/toaster.tsx (shadcn/ui)
// app/layout.tsx에 <Toaster /> 추가

import { Toaster } from "@/components/ui/toaster"

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  )
}
```

### 3.2 Toast Hook Usage

```tsx
import { useToast } from "@/components/ui/use-toast"

function MyComponent() {
  const { toast } = useToast()

  const handleAction = async () => {
    try {
      await someAction()
      toast({
        title: "저장 완료",
        description: "변경사항이 저장되었어요",
      })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "저장 실패",
        description: "다시 시도해 주세요",
      })
    }
  }
}
```

### 3.3 Toast Messages by Action

#### Login

| State | Variant | Title | Description |
|-------|---------|-------|-------------|
| Success | default | 로그인 성공 | 환영합니다, {name}님! |
| Error - Wrong credentials | destructive | 로그인 실패 | 이메일 또는 비밀번호를 확인해 주세요 |
| Error - Network | destructive | 연결 오류 | 네트워크 연결을 확인해 주세요 |
| Error - Server | destructive | 서버 오류 | 잠시 후 다시 시도해 주세요 |

```tsx
// login success
toast({
  title: "로그인 성공",
  description: `환영합니다, ${user.name}님!`,
})

// login error
toast({
  variant: "destructive",
  title: "로그인 실패",
  description: "이메일 또는 비밀번호를 확인해 주세요",
})
```

#### Create/Update Task

| State | Variant | Title | Description |
|-------|---------|-------|-------------|
| Create Success | default | 작업 생성 완료 | "{title}" 작업이 생성되었어요 |
| Update Success | default | 변경 완료 | 작업이 수정되었어요 |
| Error | destructive | 저장 실패 | 다시 시도해 주세요 |

```tsx
// create task
toast({
  title: "작업 생성 완료",
  description: `"${task.title}" 작업이 생성되었어요`,
})

// update task
toast({
  title: "변경 완료",
  description: "작업이 수정되었어요",
})
```

#### Move Task

| State | Variant | Title | Description |
|-------|---------|-------|-------------|
| Success | default | 이동 완료 | "{column}"(으)로 이동했어요 |
| Error | destructive | 이동 실패 | 다시 시도해 주세요 |

```tsx
// move task
toast({
  title: "이동 완료",
  description: `"${targetColumn.name}"(으)로 이동했어요`,
})
```

#### Create Calendar Event

| State | Variant | Title | Description |
|-------|---------|-------|-------------|
| Success | default | 일정 추가 완료 | {date}에 일정이 추가되었어요 |
| Error | destructive | 일정 추가 실패 | 다시 시도해 주세요 |

```tsx
// create event
toast({
  title: "일정 추가 완료",
  description: `${format(event.date, 'M월 d일')}에 일정이 추가되었어요`,
})
```

#### Submit Approval Request

| State | Variant | Title | Description |
|-------|---------|-------|-------------|
| Submit Success | default | 승인 요청 완료 | 승인 요청이 제출되었어요 |
| Approve Success | default | 승인 완료 | 요청이 승인되었어요 |
| Reject Success | default | 반려 완료 | 요청이 반려되었어요 |
| Error | destructive | 요청 실패 | 다시 시도해 주세요 |

```tsx
// submit approval
toast({
  title: "승인 요청 완료",
  description: "승인 요청이 제출되었어요",
})

// approve
toast({
  title: "승인 완료",
  description: "요청이 승인되었어요",
})

// reject
toast({
  title: "반려 완료",
  description: "요청이 반려되었어요",
})
```

### 3.4 Toast with Action

```tsx
// 실행 취소 가능한 토스트
toast({
  title: "작업 삭제됨",
  description: "작업이 삭제되었어요",
  action: (
    <ToastAction altText="실행 취소" onClick={handleUndo}>
      실행 취소
    </ToastAction>
  ),
})
```

---

## 4. Dialog / Modal Feedback

### 4.1 Confirmation Dialogs

```tsx
// 삭제 확인
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive" size="sm">
      <Trash2 className="h-4 w-4" />
    </Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>정말 삭제할까요?</AlertDialogTitle>
      <AlertDialogDescription>
        이 작업은 되돌릴 수 없어요. 정말 삭제하시겠어요?
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>취소</AlertDialogCancel>
      <AlertDialogAction onClick={handleDelete}>
        삭제
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

### 4.2 Dialog Messages (Korean)

| Action | Title | Description | Confirm | Cancel |
|--------|-------|-------------|---------|--------|
| 작업 삭제 | 작업을 삭제할까요? | 삭제된 작업은 복구할 수 없어요 | 삭제 | 취소 |
| 일정 삭제 | 일정을 삭제할까요? | 이 일정이 영구적으로 삭제돼요 | 삭제 | 취소 |
| 로그아웃 | 로그아웃 할까요? | 저장하지 않은 변경사항이 있을 수 있어요 | 로그아웃 | 취소 |
| 승인 요청 반려 | 요청을 반려할까요? | 반려 사유를 입력해 주세요 | 반려 | 취소 |
| 변경사항 취소 | 변경을 취소할까요? | 수정한 내용이 저장되지 않아요 | 취소하기 | 계속 수정 |

---

## 5. Inline Feedback

### 5.1 Form Validation

```tsx
// 실시간 유효성 검사 피드백
<div className="space-y-2">
  <Label htmlFor="email">이메일</Label>
  <Input
    id="email"
    type="email"
    className={cn(
      errors.email && "border-rose-500 focus-visible:ring-rose-500"
    )}
  />
  {errors.email && (
    <p className="text-sm text-rose-500 flex items-center gap-1">
      <AlertCircle className="h-4 w-4" />
      {errors.email.message}
    </p>
  )}
</div>
```

**Validation Messages (Korean):**

| Field | Error | Message |
|-------|-------|---------|
| 이메일 | Required | 이메일을 입력해 주세요 |
| 이메일 | Invalid | 올바른 이메일 형식이 아니에요 |
| 비밀번호 | Required | 비밀번호를 입력해 주세요 |
| 비밀번호 | Too short | 비밀번호는 8자 이상이어야 해요 |
| 제목 | Required | 제목을 입력해 주세요 |
| 제목 | Too long | 제목은 100자 이하로 입력해 주세요 |
| 날짜 | Required | 날짜를 선택해 주세요 |
| 날짜 | Past date | 과거 날짜는 선택할 수 없어요 |

### 5.2 Success Indicators

```tsx
// 저장 성공 인라인 표시
<div className="flex items-center gap-2 text-emerald-600">
  <CheckCircle className="h-4 w-4" />
  <span className="text-sm">저장됨</span>
</div>

// 자동 저장 표시
<div className="flex items-center gap-2 text-slate-500 text-sm">
  <Cloud className="h-4 w-4" />
  <span>자동 저장됨 · 방금 전</span>
</div>
```

---

## 6. Progress Indicators

### 6.1 Step Progress

```tsx
// 다단계 폼 진행 표시
<div className="flex items-center gap-2">
  {steps.map((step, index) => (
    <React.Fragment key={step.id}>
      <div
        className={cn(
          "flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium",
          index < currentStep
            ? "bg-primary text-white"
            : index === currentStep
            ? "bg-primary text-white ring-4 ring-primary/20"
            : "bg-slate-100 text-slate-400"
        )}
      >
        {index < currentStep ? (
          <Check className="h-4 w-4" />
        ) : (
          index + 1
        )}
      </div>
      {index < steps.length - 1 && (
        <div
          className={cn(
            "flex-1 h-0.5",
            index < currentStep ? "bg-primary" : "bg-slate-200"
          )}
        />
      )}
    </React.Fragment>
  ))}
</div>
```

### 6.2 Upload Progress

```tsx
// 파일 업로드 진행률
<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span className="text-slate-600">{file.name}</span>
    <span className="text-slate-500">{progress}%</span>
  </div>
  <Progress value={progress} className="h-2" />
</div>
```

---

## 7. Implementation Checklist

### Phase 1: Core Components

- [ ] Toast provider 설정 (`app/layout.tsx`)
- [ ] `useToast` 훅 설정
- [ ] Skeleton 컴포넌트
- [ ] EmptyState 컴포넌트
- [ ] AlertDialog 컴포넌트

### Phase 2: Page Integration

#### Login Page
- [ ] Button loading state
- [ ] Form validation messages
- [ ] Login success/error toast
- [ ] Network error handling

#### Tasks Page
- [ ] Board skeleton loader
- [ ] Empty column state
- [ ] Empty "My Tasks" state
- [ ] Task create/update toast
- [ ] Task move toast
- [ ] Task delete confirmation + toast
- [ ] Card loading state (moving)

#### Calendar Page
- [ ] Calendar skeleton
- [ ] Empty day state
- [ ] Empty month state
- [ ] Event create toast
- [ ] Event delete confirmation + toast

#### Approvals Page
- [ ] List skeleton
- [ ] Empty state
- [ ] Submit approval toast
- [ ] Approve/Reject confirmation
- [ ] Decision toast

### Phase 3: Polish

- [ ] Toast 애니메이션 (Framer Motion)
- [ ] Skeleton shimmer 효과
- [ ] Empty state 일러스트레이션
- [ ] 역할별 빈 상태 메시지

---

## 8. Code Patterns

### Toast Utility

```tsx
// lib/toast-utils.ts
import { toast } from "@/components/ui/use-toast"

export const showSuccess = (title: string, description?: string) => {
  toast({ title, description })
}

export const showError = (title: string, description?: string) => {
  toast({ variant: "destructive", title, description })
}

export const showTaskCreated = (title: string) => {
  toast({
    title: "작업 생성 완료",
    description: `"${title}" 작업이 생성되었어요`,
  })
}

export const showTaskMoved = (columnName: string) => {
  toast({
    title: "이동 완료",
    description: `"${columnName}"(으)로 이동했어요`,
  })
}

export const showEventCreated = (date: Date) => {
  toast({
    title: "일정 추가 완료",
    description: `${format(date, 'M월 d일')}에 일정이 추가되었어요`,
  })
}

export const showApprovalSubmitted = () => {
  toast({
    title: "승인 요청 완료",
    description: "승인 요청이 제출되었어요",
  })
}

export const showNetworkError = () => {
  toast({
    variant: "destructive",
    title: "연결 오류",
    description: "네트워크 연결을 확인해 주세요",
  })
}
```

### Async Action Pattern

```tsx
// 비동기 액션 패턴
const handleCreateTask = async (data: TaskCreate) => {
  setIsLoading(true)

  try {
    const task = await api.post<Task>('/tasks', data)
    showTaskCreated(task.title)
    router.refresh()
  } catch (error) {
    if (error instanceof ApiError) {
      showError("작업 생성 실패", error.message)
    } else {
      showNetworkError()
    }
  } finally {
    setIsLoading(false)
  }
}
```

---

*Document Version: 1.0*
*Last Updated: 2024-01*
