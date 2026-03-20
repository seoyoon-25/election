"use client";

import Link from "next/link";
import { Plus, ArrowRight, CheckSquare } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  StatusBadge,
  PriorityBadge,
  DueDateDisplay,
  EmptyState,
  ErrorState,
  TaskCardSkeleton,
} from "@/components/common";
import { cn } from "@/lib/utils";

interface Task {
  id: string;
  title: string;
  status: "backlog" | "todo" | "in_progress" | "review" | "done";
  priority: "low" | "medium" | "high" | "urgent";
  due_date?: string;
}

interface MyTasksWidgetProps {
  tasks: Task[];
  isLoading?: boolean;
  error?: Error | null;
  campaignId: string;
  onTaskClick?: (taskId: string) => void;
  onAddTask?: () => void;
}

// 우선순위 색상 바
const priorityBorderColors = {
  low: "border-l-green-500",
  medium: "border-l-yellow-500",
  high: "border-l-orange-500",
  urgent: "border-l-red-500",
};

export function MyTasksWidget({
  tasks,
  isLoading,
  error,
  campaignId,
  onTaskClick,
  onAddTask,
}: MyTasksWidgetProps) {
  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <CheckSquare className="h-4 w-4 text-primary" />
          내 태스크
        </CardTitle>
        {onAddTask && (
          <Button variant="ghost" size="sm" onClick={onAddTask}>
            <Plus className="h-4 w-4 mr-1" />
            추가
          </Button>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <TaskCardSkeleton key={i} />
            ))}
          </div>
        )}

        {error && (
          <ErrorState
            message="태스크를 불러오지 못했습니다"
            onRetry={() => window.location.reload()}
          />
        )}

        {!isLoading && !error && tasks.length === 0 && (
          <EmptyState
            title="할 일이 없습니다"
            description="새로운 태스크를 만들어 시작하세요"
            action={
              onAddTask
                ? { label: "태스크 만들기", onClick: onAddTask }
                : undefined
            }
          />
        )}

        {!isLoading && !error && tasks.length > 0 && (
          <>
            <div className="space-y-2 flex-1">
              {tasks.slice(0, 5).map((task) => (
                <TaskItem
                  key={task.id}
                  task={task}
                  onClick={() => onTaskClick?.(task.id)}
                />
              ))}
            </div>
            <div className="pt-3 mt-auto border-t">
              <Link
                href={`/c/${campaignId}/my-tasks`}
                className="flex items-center justify-center text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                전체보기
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function TaskItem({
  task,
  onClick,
}: {
  task: Task;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "p-3 rounded-md border bg-card cursor-pointer hover:bg-accent/50 transition-colors",
        "border-l-4",
        priorityBorderColors[task.priority]
      )}
    >
      <p className="font-medium text-sm line-clamp-1 mb-1.5">{task.title}</p>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <PriorityBadge priority={task.priority} size="sm" showIcon={false} />
          <StatusBadge status={task.status} size="sm" />
        </div>
        {task.due_date && (
          <DueDateDisplay dueDate={task.due_date} showIcon={false} />
        )}
      </div>
    </div>
  );
}
