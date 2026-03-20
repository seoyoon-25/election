"use client";

import { GripVertical, MessageSquare, Paperclip } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  StatusBadge,
  PriorityBadge,
  DueDateDisplay,
  UserAvatarGroup,
} from "@/components/common";
import { cn, getDueStatus } from "@/lib/utils";

interface User {
  id: string;
  name: string;
  avatar_url?: string;
}

interface TaskCardProps {
  task: {
    id: string;
    title: string;
    status: "backlog" | "todo" | "in_progress" | "review" | "done";
    priority: "low" | "medium" | "high" | "urgent";
    due_date?: string;
    assignees?: User[];
    comments_count?: number;
    attachments_count?: number;
    tags?: string[];
  };
  isDragging?: boolean;
  onClick?: () => void;
  showStatus?: boolean;
  className?: string;
}

// 우선순위 색상 바
const priorityBorderColors = {
  low: "border-l-green-500",
  medium: "border-l-yellow-500",
  high: "border-l-orange-500",
  urgent: "border-l-red-500",
};

export function TaskCard({
  task,
  isDragging,
  onClick,
  showStatus = false,
  className,
}: TaskCardProps) {
  const dueStatus = getDueStatus(task.due_date);
  const isOverdue = dueStatus === "overdue";
  const isDueToday = dueStatus === "today";

  return (
    <Card
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label={`태스크: ${task.title}${task.due_date ? `, 마감일: ${task.due_date}` : ""}`}
      className={cn(
        "p-3 cursor-pointer transition-all border-l-4",
        priorityBorderColors[task.priority],
        "hover:shadow-md hover:border-primary/50",
        "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
        isDragging && "shadow-lg ring-2 ring-primary rotate-1 scale-105",
        isOverdue && "ring-1 ring-red-300 bg-red-50/50",
        isDueToday && "bg-amber-50/50",
        className
      )}
    >
      {/* 드래그 핸들 + 제목 */}
      <div className="flex items-start gap-2">
        <GripVertical className="h-4 w-4 text-muted-foreground/50 shrink-0 mt-0.5 cursor-grab" />
        <p className="font-medium text-sm line-clamp-2 flex-1">{task.title}</p>
      </div>

      {/* 마감일 */}
      {task.due_date && (
        <div className="mt-2">
          <DueDateDisplay dueDate={task.due_date} showIcon />
        </div>
      )}

      {/* 배지들 */}
      <div className="flex items-center gap-1.5 mt-2 flex-wrap">
        <PriorityBadge priority={task.priority} size="sm" showIcon={false} />
        {showStatus && <StatusBadge status={task.status} size="sm" />}
        {task.tags?.slice(0, 2).map((tag) => (
          <span
            key={tag}
            className="px-1.5 py-0.5 text-[10px] bg-muted text-muted-foreground rounded"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* 하단: 담당자 + 메타 */}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-border/50">
        {/* 담당자 */}
        {task.assignees && task.assignees.length > 0 ? (
          <UserAvatarGroup users={task.assignees} max={3} size="sm" />
        ) : (
          <span className="text-xs text-muted-foreground">담당자 없음</span>
        )}

        {/* 코멘트/첨부 카운트 */}
        <div className="flex items-center gap-2 text-muted-foreground">
          {task.comments_count !== undefined && task.comments_count > 0 && (
            <span className="flex items-center gap-0.5 text-xs">
              <MessageSquare className="h-3 w-3" />
              {task.comments_count}
            </span>
          )}
          {task.attachments_count !== undefined && task.attachments_count > 0 && (
            <span className="flex items-center gap-0.5 text-xs">
              <Paperclip className="h-3 w-3" />
              {task.attachments_count}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
