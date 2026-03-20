"use client";

import { TaskColumn } from "./TaskColumn";
import { LoadingState, ErrorState, EmptyState } from "@/components/common";

type TaskStatus = "backlog" | "todo" | "in_progress" | "review" | "done";

interface User {
  id: string;
  name: string;
  avatar_url?: string;
}

interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  priority: "low" | "medium" | "high" | "urgent";
  due_date?: string;
  assignees?: User[];
  comments_count?: number;
  attachments_count?: number;
  tags?: string[];
}

interface TaskBoardProps {
  tasks: Task[];
  isLoading?: boolean;
  error?: Error | null;
  onTaskClick?: (taskId: string) => void;
  onAddTask?: (status?: TaskStatus) => void;
}

const columnOrder: TaskStatus[] = [
  "backlog",
  "todo",
  "in_progress",
  "review",
  "done",
];

export function TaskBoard({
  tasks,
  isLoading,
  error,
  onTaskClick,
  onAddTask,
}: TaskBoardProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingState text="태스크를 불러오는 중..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <ErrorState
          message="태스크를 불러오지 못했습니다"
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <EmptyState
          title="태스크가 없습니다"
          description="새로운 태스크를 만들어 프로젝트를 시작하세요"
          action={
            onAddTask
              ? { label: "첫 태스크 만들기", onClick: () => onAddTask() }
              : undefined
          }
        />
      </div>
    );
  }

  // 상태별로 태스크 그룹화
  const tasksByStatus = columnOrder.reduce((acc, status) => {
    acc[status] = tasks.filter((task) => task.status === status);
    return acc;
  }, {} as Record<TaskStatus, Task[]>);

  return (
    <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin">
      {columnOrder.map((status) => (
        <TaskColumn
          key={status}
          status={status}
          tasks={tasksByStatus[status]}
          onTaskClick={onTaskClick}
          onAddTask={() => onAddTask?.(status)}
        />
      ))}
    </div>
  );
}
