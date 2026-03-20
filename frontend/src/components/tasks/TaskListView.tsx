"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  StatusBadge,
  PriorityBadge,
  DueDateDisplay,
  UserAvatarGroup,
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/common";
import { cn } from "@/lib/utils";

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
}

interface TaskListViewProps {
  tasks: Task[];
  isLoading?: boolean;
  error?: Error | null;
  onTaskClick?: (taskId: string) => void;
  onAddTask?: () => void;
}

export function TaskListView({
  tasks,
  isLoading,
  error,
  onTaskClick,
  onAddTask,
}: TaskListViewProps) {
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
              ? { label: "첫 태스크 만들기", onClick: onAddTask }
              : undefined
          }
        />
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[40%]">태스크</TableHead>
            <TableHead className="w-[12%]">상태</TableHead>
            <TableHead className="w-[12%]">우선순위</TableHead>
            <TableHead className="w-[18%]">담당자</TableHead>
            <TableHead className="w-[18%]">마감일</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((task) => (
            <TableRow
              key={task.id}
              className="cursor-pointer hover:bg-muted/50"
              onClick={() => onTaskClick?.(task.id)}
            >
              <TableCell className="font-medium">
                <p className="line-clamp-1">{task.title}</p>
              </TableCell>
              <TableCell>
                <StatusBadge status={task.status} size="sm" />
              </TableCell>
              <TableCell>
                <PriorityBadge priority={task.priority} size="sm" />
              </TableCell>
              <TableCell>
                {task.assignees && task.assignees.length > 0 ? (
                  <UserAvatarGroup users={task.assignees} max={2} size="sm" />
                ) : (
                  <span className="text-xs text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell>
                {task.due_date ? (
                  <DueDateDisplay dueDate={task.due_date} />
                ) : (
                  <span className="text-xs text-muted-foreground">-</span>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
