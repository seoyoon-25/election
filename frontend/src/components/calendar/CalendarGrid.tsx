"use client";

import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
  format,
} from "date-fns";
import { ko } from "date-fns/locale";
import { cn } from "@/lib/utils";

interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  type?: "meeting" | "campaign" | "deadline" | "briefing" | "other";
}

interface CalendarGridProps {
  currentDate: Date;
  selectedDate?: Date;
  events: CalendarEvent[];
  onDateSelect: (date: Date) => void;
  onEventClick?: (eventId: string) => void;
}

const eventTypeColors: Record<string, string> = {
  meeting: "bg-blue-500",
  campaign: "bg-orange-500",
  deadline: "bg-red-500",
  briefing: "bg-purple-500",
  other: "bg-gray-500",
};

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

export function CalendarGrid({
  currentDate,
  selectedDate,
  events,
  onDateSelect,
  onEventClick,
}: CalendarGridProps) {
  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarStart = startOfWeek(monthStart, { locale: ko });
  const calendarEnd = endOfWeek(monthEnd, { locale: ko });

  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  const getEventsForDay = (date: Date) => {
    return events.filter((event) => {
      const eventDate = new Date(event.start_time);
      return isSameDay(eventDate, date);
    });
  };

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 bg-muted">
        {WEEKDAYS.map((day, index) => (
          <div
            key={day}
            className={cn(
              "py-2 text-center text-sm font-medium",
              index === 0 && "text-red-500",
              index === 6 && "text-blue-500"
            )}
          >
            {day}
          </div>
        ))}
      </div>

      {/* 날짜 그리드 */}
      <div className="grid grid-cols-7">
        {days.map((day, index) => {
          const dayEvents = getEventsForDay(day);
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isSelected = selectedDate && isSameDay(day, selectedDate);
          const isCurrentDay = isToday(day);
          const dayOfWeek = day.getDay();

          return (
            <div
              key={day.toISOString()}
              onClick={() => onDateSelect(day)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onDateSelect(day);
                }
              }}
              role="button"
              tabIndex={0}
              aria-label={`${format(day, "M월 d일", { locale: ko })}${dayEvents.length > 0 ? `, ${dayEvents.length}개 일정` : ""}`}
              aria-selected={isSelected}
              className={cn(
                "min-h-[100px] p-1 border-r border-b cursor-pointer transition-colors",
                "hover:bg-accent/50",
                "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-inset",
                !isCurrentMonth && "bg-muted/30 text-muted-foreground",
                isSelected && "ring-2 ring-primary ring-inset",
                isCurrentDay && "bg-primary/5"
              )}
            >
              {/* 날짜 숫자 */}
              <div className="flex justify-center mb-1">
                <span
                  className={cn(
                    "w-7 h-7 flex items-center justify-center text-sm",
                    isCurrentDay &&
                      "bg-primary text-primary-foreground rounded-full font-bold",
                    dayOfWeek === 0 && !isCurrentDay && "text-red-500",
                    dayOfWeek === 6 && !isCurrentDay && "text-blue-500"
                  )}
                >
                  {format(day, "d")}
                </span>
              </div>

              {/* 일정 미리보기 */}
              <div className="space-y-0.5">
                {dayEvents.slice(0, 2).map((event) => (
                  <button
                    key={event.id}
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEventClick?.(event.id);
                    }}
                    className={cn(
                      "w-full text-left text-[10px] px-1 py-0.5 rounded truncate text-white cursor-pointer hover:opacity-80",
                      "focus:outline-none focus:ring-1 focus:ring-white",
                      eventTypeColors[event.type || "other"]
                    )}
                    title={event.title}
                    aria-label={`일정: ${event.title}`}
                  >
                    {event.title}
                  </button>
                ))}
                {dayEvents.length > 2 && (
                  <div className="text-[10px] text-muted-foreground text-center">
                    +{dayEvents.length - 2}개 더
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
