"use client";

import { memo } from "react";
import Link from "next/link";
import { Plus, ArrowRight, Calendar, MapPin, Clock } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, CardSkeleton } from "@/components/common";
import { formatTime } from "@/lib/utils";

interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  location?: string;
  is_all_day?: boolean;
}

interface TodayScheduleWidgetProps {
  events: CalendarEvent[];
  isLoading?: boolean;
  error?: Error | null;
  campaignId: string;
  onEventClick?: (eventId: string) => void;
  onAddEvent?: () => void;
}

export const TodayScheduleWidget = memo(function TodayScheduleWidget({
  events,
  isLoading,
  error,
  campaignId,
  onEventClick,
  onAddEvent,
}: TodayScheduleWidgetProps) {
  const today = new Date();
  const formattedDate = today.toLocaleDateString("ko-KR", {
    month: "long",
    day: "numeric",
    weekday: "short",
  });

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Calendar className="h-4 w-4 text-primary" />
          오늘 일정
          <span className="text-xs font-normal text-muted-foreground">
            {formattedDate}
          </span>
        </CardTitle>
        {onAddEvent && (
          <Button variant="ghost" size="sm" onClick={onAddEvent}>
            <Plus className="h-4 w-4 mr-1" />
            추가
          </Button>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <CardSkeleton key={i} className="h-20" />
            ))}
          </div>
        )}

        {error && (
          <ErrorState
            message="일정을 불러오지 못했습니다"
            onRetry={() => window.location.reload()}
          />
        )}

        {!isLoading && !error && events.length === 0 && (
          <EmptyState
            title="오늘 일정이 없습니다"
            description="여유로운 하루를 보내세요"
            icon={<Calendar className="h-8 w-8 text-muted-foreground" />}
          />
        )}

        {!isLoading && !error && events.length > 0 && (
          <>
            <div className="space-y-1 flex-1">
              {events.map((event, index) => (
                <EventItem
                  key={event.id}
                  event={event}
                  isFirst={index === 0}
                  onClick={() => onEventClick?.(event.id)}
                />
              ))}
            </div>
            <div className="pt-3 mt-auto border-t">
              <Link
                href={`/c/${campaignId}/my-calendar`}
                className="flex items-center justify-center text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                전체 일정
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
});

const EventItem = memo(function EventItem({
  event,
  isFirst,
  onClick,
}: {
  event: CalendarEvent;
  isFirst: boolean;
  onClick?: () => void;
}) {
  const startTime = formatTime(event.start_time);
  const endTime = formatTime(event.end_time);

  return (
    <div
      onClick={onClick}
      className="relative pl-4 py-2 cursor-pointer hover:bg-accent/50 rounded-md transition-colors"
    >
      {/* 타임라인 선 */}
      <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-border" />
      <div className="absolute left-[-3px] top-3 w-2 h-2 rounded-full bg-primary" />

      {/* 시간 */}
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
        <Clock className="h-3 w-3" />
        {event.is_all_day ? (
          <span>종일</span>
        ) : (
          <span>
            {startTime} - {endTime}
          </span>
        )}
      </div>

      {/* 제목 */}
      <p className="font-medium text-sm line-clamp-1">{event.title}</p>

      {/* 장소 */}
      {event.location && (
        <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
          <MapPin className="h-3 w-3" />
          <span className="truncate">{event.location}</span>
        </div>
      )}
    </div>
  );
});
