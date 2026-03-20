"use client";

import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { LayoutGrid, List, GanttChart } from "lucide-react";

type Priority = "low" | "medium" | "high" | "urgent";
type ViewMode = "board" | "list" | "timeline";

interface TaskFiltersProps {
  filters: {
    assignee?: string;
    priority?: Priority;
    search?: string;
  };
  onFiltersChange: (filters: TaskFiltersProps["filters"]) => void;
  isMyTasksOnly: boolean;
  onMyTasksToggle: (checked: boolean) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  assigneeOptions?: Array<{ id: string; name: string }>;
}

export function TaskFilters({
  filters,
  onFiltersChange,
  isMyTasksOnly,
  onMyTasksToggle,
  viewMode,
  onViewModeChange,
  assigneeOptions = [],
}: TaskFiltersProps) {
  const activeFiltersCount = [
    filters.assignee,
    filters.priority,
    filters.search,
  ].filter(Boolean).length;

  const clearFilters = () => {
    onFiltersChange({});
  };

  return (
    <div className="space-y-4">
      {/* 상단: 검색 + 뷰 전환 + CTA */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* 검색 */}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="태스크 검색..."
            className="pl-8"
            value={filters.search || ""}
            onChange={(e) =>
              onFiltersChange({ ...filters, search: e.target.value || undefined })
            }
          />
        </div>

        {/* 필터들 */}
        <Select
          value={filters.priority || "all"}
          onValueChange={(value) =>
            onFiltersChange({
              ...filters,
              priority: value === "all" ? undefined : (value as Priority),
            })
          }
        >
          <SelectTrigger className="w-[130px]">
            <SelectValue placeholder="우선순위" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체</SelectItem>
            <SelectItem value="urgent">긴급</SelectItem>
            <SelectItem value="high">높음</SelectItem>
            <SelectItem value="medium">보통</SelectItem>
            <SelectItem value="low">낮음</SelectItem>
          </SelectContent>
        </Select>

        {assigneeOptions.length > 0 && (
          <Select
            value={filters.assignee || "all"}
            onValueChange={(value) =>
              onFiltersChange({
                ...filters,
                assignee: value === "all" ? undefined : value,
              })
            }
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="담당자" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체</SelectItem>
              {assigneeOptions.map((user) => (
                <SelectItem key={user.id} value={user.id}>
                  {user.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {/* 필터 초기화 */}
        {activeFiltersCount > 0 && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="h-4 w-4 mr-1" />
            필터 초기화
            <Badge variant="secondary" className="ml-1">
              {activeFiltersCount}
            </Badge>
          </Button>
        )}

        {/* 스페이서 */}
        <div className="flex-1" />

        {/* 내 태스크만 */}
        <div className="flex items-center gap-2">
          <Checkbox
            id="myTasksOnly"
            checked={isMyTasksOnly}
            onCheckedChange={(checked) => onMyTasksToggle(checked as boolean)}
          />
          <label
            htmlFor="myTasksOnly"
            className="text-sm cursor-pointer select-none"
          >
            내 태스크만
          </label>
        </div>

        {/* 뷰 전환 */}
        <ToggleGroup
          type="single"
          value={viewMode}
          onValueChange={(value) => value && onViewModeChange(value as ViewMode)}
          className="border rounded-md"
        >
          <ToggleGroupItem value="board" aria-label="보드 뷰" className="px-3">
            <LayoutGrid className="h-4 w-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="list" aria-label="목록 뷰" className="px-3">
            <List className="h-4 w-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="timeline" aria-label="타임라인 뷰" className="px-3">
            <GanttChart className="h-4 w-4" />
          </ToggleGroupItem>
        </ToggleGroup>
      </div>
    </div>
  );
}
