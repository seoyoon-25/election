"use client";

import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TaskCard } from "./TaskCard";
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
  comments_count?: number;
  attachments_count?: number;
  tags?: string[];
}

interface TaskColumnProps {
  status: TaskStatus;
  tasks: Task[];
  onTaskClick?: (taskId: string) => void;
  onAddTask?: () => void;
}

const statusConfig: Record<
  TaskStatus,
  { label: string; color: string; bgColor: string }
> = {
  backlog: {
    label: "대기",
    color: "bg-gray-500",
    bgColor: "bg-gray-50",
  },
  todo: {
    label: "예정",
    color: "bg-blue-500",
    bgColor: "bg-blue-50",
  },
  in_progress: {
    label: "진행중",
    color: "bg-indigo-500",
    bgColor: "bg-indigo-50",
  },
  review: {
    label: "검토",
    color: "bg-purple-500",
    bgColor: "bg-purple-50",
  },
  done: {
    label: "완료",
    color: "bg-green-500",
    bgColor: "bg-green-50",
  },
};

export function TaskColumn({
  status,
  tasks,
  onTaskClick,
  onAddTask,
}: TaskColumnProps) {
  const config = statusConfig[status];

  return (
    <div className="flex flex-col min-w-[280px] max-w-[320px] h-full">
      {/* 칼럼 헤더 */}
      <div
        className={cn(
          "flex items-center justify-between p-3 rounded-t-lg",
          config.bgColor
        )}
      >
        <div className="flex items-center gap-2">
          <div className={cn("w-2 h-2 rounded-full", config.color)} />
          <h3 className="font-medium text-sm">{config.label}</h3>
          <span className="text-xs text-muted-foreground bg-background px-1.5 py-0.5 rounded">
            {tasks.length}
          </span>
        </div>
        {onAddTask && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={onAddTask}
            aria-label={`${config.label} 태스크 추가`}
          >
            <Plus className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* 칼럼 바디 */}
      <div
        className={cn(
          "flex-1 p-2 space-y-2 overflow-y-auto rounded-b-lg border border-t-0 border-border/50 min-h-[200px]",
          config.bgColor,
          "bg-opacity-30"
        )}
      >
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onClick={() => onTaskClick?.(task.id)}
          />
        ))}

        {/* 빈 상태 - 태스크 추가 유도 */}
        {tasks.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-sm text-muted-foreground mb-2">
              태스크가 없습니다
            </p>
            {onAddTask && (
              <Button variant="outline" size="sm" onClick={onAddTask}>
                <Plus className="h-4 w-4 mr-1" />
                태스크 추가
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
