"use client";

import { format } from "date-fns";
import { ko } from "date-fns/locale";
import { Clock, MapPin, Users, Plus, Edit, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { UserAvatarGroup, EmptyState } from "@/components/common";
import { cn } from "@/lib/utils";

interface User {
  id: string;
  name: string;
  avatar_url?: string;
}

interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  location?: string;
  attendees?: User[];
  type?: "meeting" | "campaign" | "deadline" | "briefing" | "other";
  is_all_day?: boolean;
}

interface EventDetailPanelProps {
  date: Date;
  events: CalendarEvent[];
  onEventClick?: (eventId: string) => void;
  onEventEdit?: (eventId: string) => void;
  onEventDelete?: (eventId: string) => void;
  onAddEvent?: () => void;
}

const eventTypeColors: Record<string, string> = {
  meeting: "bg-blue-500",
  campaign: "bg-orange-500",
  deadline: "bg-red-500",
  briefing: "bg-purple-500",
  other: "bg-gray-500",
};

const eventTypeLabels: Record<string, string> = {
  meeting: "회의",
  campaign: "유세",
  deadline: "마감",
  briefing: "브리핑",
  other: "기타",
};

export function EventDetailPanel({
  date,
  events,
  onEventClick,
  onEventEdit,
  onEventDelete,
  onAddEvent,
}: EventDetailPanelProps) {
  const formattedDate = format(date, "M월 d일 EEEE", { locale: ko });

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          {formattedDate}
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          {events.length > 0 ? `${events.length}개의 일정` : "일정 없음"}
        </p>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto space-y-3">
        {events.length === 0 ? (
          <EmptyState
            title="일정이 없습니다"
            description="이 날에 새 일정을 추가해보세요"
            action={
              onAddEvent
                ? { label: "일정 추가", onClick: onAddEvent }
                : undefined
            }
          />
        ) : (
          <>
            {events.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onClick={() => onEventClick?.(event.id)}
                onEdit={() => onEventEdit?.(event.id)}
                onDelete={() => onEventDelete?.(event.id)}
              />
            ))}
            {onAddEvent && (
              <Button
                variant="outline"
                className="w-full mt-2"
                onClick={onAddEvent}
              >
                <Plus className="h-4 w-4 mr-2" />
                이 날에 일정 추가
              </Button>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function EventCard({
  event,
  onClick,
  onEdit,
  onDelete,
}: {
  event: CalendarEvent;
  onClick?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}) {
  const startTime = format(new Date(event.start_time), "HH:mm");
  const endTime = format(new Date(event.end_time), "HH:mm");
  const typeColor = eventTypeColors[event.type || "other"];
  const typeLabel = eventTypeLabels[event.type || "other"];

  return (
    <div
      onClick={onClick}
      className="p-3 rounded-lg border bg-card hover:bg-accent/50 cursor-pointer transition-colors"
    >
      {/* 상단: 시간 + 타입 */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          {event.is_all_day ? (
            <span>종일</span>
          ) : (
            <span>
              {startTime} - {endTime}
            </span>
          )}
        </div>
        <div
          className={cn(
            "px-2 py-0.5 rounded text-[10px] font-medium text-white",
            typeColor
          )}
        >
          {typeLabel}
        </div>
      </div>

      {/* 제목 */}
      <h4 className="font-medium text-sm mb-2">{event.title}</h4>

      {/* 설명 */}
      {event.description && (
        <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
          {event.description}
        </p>
      )}

      {/* 장소 */}
      {event.location && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
          <MapPin className="h-3 w-3" />
          <span className="truncate">{event.location}</span>
        </div>
      )}

      {/* 참석자 */}
      {event.attendees && event.attendees.length > 0 && (
        <div className="flex items-center gap-2 mb-2">
          <Users className="h-3 w-3 text-muted-foreground" />
          <UserAvatarGroup users={event.attendees} max={4} size="sm" />
        </div>
      )}

      {/* 액션 버튼 */}
      <div className="flex items-center justify-end gap-1 pt-2 border-t mt-2">
        {onEdit && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={(e) => {
              e.stopPropagation();
              onEdit();
            }}
          >
            <Edit className="h-3 w-3 mr-1" />
            수정
          </Button>
        )}
        {onDelete && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-destructive hover:text-destructive"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
          >
            <Trash2 className="h-3 w-3 mr-1" />
            삭제
          </Button>
        )}
      </div>
    </div>
  );
}
