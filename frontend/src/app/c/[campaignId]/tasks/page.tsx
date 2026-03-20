"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import { Plus } from "lucide-react";
import { api } from "@/lib/api";
import { Task, PaginatedResponse } from "@/types";
import { Button } from "@/components/ui/button";
import {
  TaskBoard,
  TaskListView,
  TaskFilters,
} from "@/components/tasks";

type ViewMode = "board" | "list" | "timeline";
type Priority = "low" | "medium" | "high" | "urgent";

export default function TasksPage() {
  const params = useParams();
  const campaignId = params.campaignId as string;

  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("board");
  const [isMyTasksOnly, setIsMyTasksOnly] = useState(false);
  const [filters, setFilters] = useState<{
    assignee?: string;
    priority?: Priority;
    search?: string;
  }>({});

  // 데이터 로드
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get<PaginatedResponse<Task>>(
          `/campaigns/${campaignId}/tasks?page_size=200`
        );
        setTasks(response.items || []);
      } catch (err) {
        console.error("Failed to load tasks:", err);
        setError(err instanceof Error ? err : new Error("태스크 로드 실패"));
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [campaignId]);

  // 필터링된 태스크
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      // 검색어 필터
      if (
        filters.search &&
        !task.title.toLowerCase().includes(filters.search.toLowerCase())
      ) {
        return false;
      }

      // 우선순위 필터
      if (filters.priority && task.priority !== filters.priority) {
        return false;
      }

      // 담당자 필터
      if (filters.assignee) {
        const hasAssignee = task.assignees?.some(
          (a) => a.id === filters.assignee
        );
        if (!hasAssignee) return false;
      }

      // 내 태스크만 (현재는 임시로 assignees가 있는 것만)
      // 실제로는 현재 로그인한 사용자 ID와 비교해야 함
      if (isMyTasksOnly && (!task.assignees || task.assignees.length === 0)) {
        return false;
      }

      return true;
    });
  }, [tasks, filters, isMyTasksOnly]);

  // 태스크 데이터를 컴포넌트용으로 변환
  const formattedTasks = useMemo(() => {
    return filteredTasks.map((task) => ({
      id: task.id,
      title: task.title,
      status: task.status as
        | "backlog"
        | "todo"
        | "in_progress"
        | "review"
        | "done",
      priority: task.priority as "low" | "medium" | "high" | "urgent",
      due_date: task.due_date,
      assignees: task.assignees?.map((a) => ({
        id: a.id,
        name: a.full_name || a.email,
        avatar_url: a.avatar_url,
      })),
      comments_count: task.comments_count,
      attachments_count: task.attachments_count,
      tags: task.tags,
    }));
  }, [filteredTasks]);

  // 담당자 옵션 (중복 제거)
  const assigneeOptions = useMemo(() => {
    const assigneesMap = new Map<string, { id: string; name: string }>();
    tasks.forEach((task) => {
      task.assignees?.forEach((a) => {
        if (!assigneesMap.has(a.id)) {
          assigneesMap.set(a.id, {
            id: a.id,
            name: a.full_name || a.email,
          });
        }
      });
    });
    return Array.from(assigneesMap.values());
  }, [tasks]);

  const handleTaskClick = (taskId: string) => {
    // TODO: 태스크 상세 시트 열기
    console.log("Task clicked:", taskId);
  };

  const handleAddTask = (status?: string) => {
    // TODO: 태스크 생성 다이얼로그 열기
    console.log("Add task with status:", status);
  };

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">태스크 보드</h1>
          <p className="text-muted-foreground">
            팀의 모든 태스크를 관리하세요
          </p>
        </div>
        <Button onClick={() => handleAddTask()}>
          <Plus className="h-4 w-4 mr-2" />
          새 태스크
        </Button>
      </div>

      {/* 필터 */}
      <TaskFilters
        filters={filters}
        onFiltersChange={setFilters}
        isMyTasksOnly={isMyTasksOnly}
        onMyTasksToggle={setIsMyTasksOnly}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        assigneeOptions={assigneeOptions}
      />

      {/* 태스크 뷰 */}
      {viewMode === "board" && (
        <TaskBoard
          tasks={formattedTasks}
          isLoading={loading}
          error={error}
          onTaskClick={handleTaskClick}
          onAddTask={handleAddTask}
        />
      )}

      {viewMode === "list" && (
        <TaskListView
          tasks={formattedTasks}
          isLoading={loading}
          error={error}
          onTaskClick={handleTaskClick}
          onAddTask={() => handleAddTask()}
        />
      )}

      {viewMode === "timeline" && (
        <div className="flex items-center justify-center h-64 border rounded-lg bg-muted/20">
          <p className="text-muted-foreground">
            타임라인 뷰는 준비 중입니다
          </p>
        </div>
      )}
    </div>
  );
}
