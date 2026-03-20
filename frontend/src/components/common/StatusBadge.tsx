import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type TaskStatus =
  | "backlog"
  | "todo"
  | "in_progress"
  | "review"
  | "done";

export type ApprovalStatus = "pending" | "approved" | "rejected";

interface StatusBadgeProps {
  status: TaskStatus | ApprovalStatus;
  size?: "sm" | "md";
  className?: string;
}

const taskStatusConfig: Record<
  TaskStatus,
  { label: string; variant: "backlog" | "todo" | "in-progress" | "review" | "done" }
> = {
  backlog: { label: "대기", variant: "backlog" },
  todo: { label: "예정", variant: "todo" },
  in_progress: { label: "진행중", variant: "in-progress" },
  review: { label: "검토", variant: "review" },
  done: { label: "완료", variant: "done" },
};

const approvalStatusConfig: Record<
  ApprovalStatus,
  { label: string; variant: "pending" | "approved" | "rejected" }
> = {
  pending: { label: "대기", variant: "pending" },
  approved: { label: "승인", variant: "approved" },
  rejected: { label: "반려", variant: "rejected" },
};

export function StatusBadge({ status, size = "md", className }: StatusBadgeProps) {
  const isTaskStatus = status in taskStatusConfig;
  const config = isTaskStatus
    ? taskStatusConfig[status as TaskStatus]
    : approvalStatusConfig[status as ApprovalStatus];

  return (
    <Badge
      variant={config.variant as any}
      className={cn(
        size === "sm" && "px-1.5 py-0 text-[10px]",
        className
      )}
    >
      {config.label}
    </Badge>
  );
}
