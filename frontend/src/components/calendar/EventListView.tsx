"use client";

import { format, isSameDay, parseISO, startOfDay } from "date-fns";
import { ko } from "date-fns/locale";
import { Clock, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/common";
import { cn } from "@/lib/utils";

interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  location?: string;
  type?: "meeting" | "campaign" | "deadline" | "briefing" | "other";
  is_all_day?: boolean;
}

interface EventListViewProps {
  events: CalendarEvent[];
  isLoading?: boolean;
  error?: Error | null;
  onEventClick?: (eventId: string) => void;
  onAddEvent?: () => void;
}

const eventTypeColors: Record<string, string> = {
  meeting: "bg-blue-100 text-blue-700",
  campaign: "bg-orange-100 text-orange-700",
  deadline: "bg-red-100 text-red-700",
  briefing: "bg-purple-100 text-purple-700",
  other: "bg-gray-100 text-gray-700",
};

const eventTypeLabels: Record<string, string> = {
  meeting: "회의",
  campaign: "유세",
  deadline: "마감",
  briefing: "브리핑",
  other: "기타",
};

export function EventListView({
  events,
  isLoading,
  error,
  onEventClick,
  onAddEvent,
}: EventListViewProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingState text="일정을 불러오는 중..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <ErrorState
          message="일정을 불러오지 못했습니다"
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <EmptyState
          title="일정이 없습니다"
          description="새로운 일정을 추가해보세요"
          action={
            onAddEvent
              ? { label: "일정 추가", onClick: onAddEvent }
              : undefined
          }
        />
      </div>
    );
  }

  // 날짜별로 그룹화
  const groupedEvents = events.reduce((groups, event) => {
    const dateKey = startOfDay(parseISO(event.start_time)).toISOString();
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(event);
    return groups;
  }, {} as Record<string, CalendarEvent[]>);

  // 날짜순 정렬
  const sortedDates = Object.keys(groupedEvents).sort();

  return (
    <div className="space-y-6">
      {sortedDates.map((dateKey) => {
        const date = new Date(dateKey);
        const dayEvents = groupedEvents[dateKey].sort(
          (a, b) =>
            new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
        );

        return (
          <div key={dateKey}>
            {/* 날짜 헤더 */}
            <div className="sticky top-0 bg-background py-2 mb-2 border-b">
              <h3 className="font-semibold text-sm">
                {format(date, "M월 d일 (EEEE)", { locale: ko })}
              </h3>
            </div>

            {/* 해당 날짜의 일정들 */}
            <div className="space-y-2">
              {dayEvents.map((event) => (
                <EventListItem
                  key={event.id}
                  event={event}
                  onClick={() => onEventClick?.(event.id)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function EventListItem({
  event,
  onClick,
}: {
  event: CalendarEvent;
  onClick?: () => void;
}) {
  const startTime = format(new Date(event.start_time), "HH:mm");
  const endTime = format(new Date(event.end_time), "HH:mm");
  const typeColor = eventTypeColors[event.type || "other"];
  const typeLabel = eventTypeLabels[event.type || "other"];

  return (
    <div
      onClick={onClick}
      className="flex items-start gap-4 p-3 rounded-lg border bg-card hover:bg-accent/50 cursor-pointer transition-colors"
    >
      {/* 시간 */}
      <div className="w-20 shrink-0 text-sm">
        {event.is_all_day ? (
          <span className="text-muted-foreground">종일</span>
        ) : (
          <div className="flex flex-col">
            <span className="font-medium">{startTime}</span>
            <span className="text-muted-foreground text-xs">{endTime}</span>
          </div>
        )}
      </div>

      {/* 콘텐츠 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-medium text-sm truncate">{event.title}</h4>
          <Badge className={cn("text-[10px]", typeColor)}>{typeLabel}</Badge>
        </div>
        {event.location && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="h-3 w-3" />
            <span className="truncate">{event.location}</span>
          </div>
        )}
      </div>
    </div>
  );
}
