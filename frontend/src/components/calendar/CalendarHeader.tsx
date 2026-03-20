"use client";

import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Checkbox } from "@/components/ui/checkbox";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

type ViewMode = "month" | "week" | "day" | "list";

interface CalendarHeaderProps {
  currentDate: Date;
  viewMode: ViewMode;
  isMyEventsOnly: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onToday: () => void;
  onViewModeChange: (mode: ViewMode) => void;
  onMyEventsToggle: (checked: boolean) => void;
  onAddEvent?: () => void;
}

export function CalendarHeader({
  currentDate,
  viewMode,
  isMyEventsOnly,
  onPrevious,
  onNext,
  onToday,
  onViewModeChange,
  onMyEventsToggle,
  onAddEvent,
}: CalendarHeaderProps) {
  const formattedDate = format(currentDate, "yyyy년 M월", { locale: ko });

  return (
    <div className="flex items-center justify-between flex-wrap gap-4">
      {/* 좌측: 날짜 네비게이션 */}
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={onToday}>
          오늘
        </Button>
        <div className="flex items-center">
          <Button variant="ghost" size="icon" onClick={onPrevious}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="font-semibold text-lg min-w-[120px] text-center">
            {formattedDate}
          </span>
          <Button variant="ghost" size="icon" onClick={onNext}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 우측: 뷰 전환 + 필터 + CTA */}
      <div className="flex items-center gap-4">
        {/* 내 일정만 */}
        <div className="flex items-center gap-2">
          <Checkbox
            id="myEventsOnly"
            checked={isMyEventsOnly}
            onCheckedChange={(checked) => onMyEventsToggle(checked as boolean)}
          />
          <label
            htmlFor="myEventsOnly"
            className="text-sm cursor-pointer select-none"
          >
            내 일정만
          </label>
        </div>

        {/* 뷰 전환 */}
        <ToggleGroup
          type="single"
          value={viewMode}
          onValueChange={(value) => value && onViewModeChange(value as ViewMode)}
          className="border rounded-md"
        >
          <ToggleGroupItem value="month" className="px-3 text-sm">
            월
          </ToggleGroupItem>
          <ToggleGroupItem value="week" className="px-3 text-sm">
            주
          </ToggleGroupItem>
          <ToggleGroupItem value="day" className="px-3 text-sm">
            일
          </ToggleGroupItem>
          <ToggleGroupItem value="list" className="px-3 text-sm">
            목록
          </ToggleGroupItem>
        </ToggleGroup>

        {/* 일정 추가 버튼 */}
        {onAddEvent && (
          <Button onClick={onAddEvent}>
            <Plus className="h-4 w-4 mr-2" />
            새 일정
          </Button>
        )}
      </div>
    </div>
  );
}
