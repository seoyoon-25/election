"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import {
  addMonths,
  subMonths,
  startOfMonth,
  endOfMonth,
  isSameDay,
} from "date-fns";
import { api } from "@/lib/api";
import { CalendarEvent as CalendarEventType } from "@/types";
import {
  CalendarHeader,
  CalendarGrid,
  EventDetailPanel,
  EventListView,
} from "@/components/calendar";
import { LoadingState } from "@/components/common";

type ViewMode = "month" | "week" | "day" | "list";

export default function CalendarPage() {
  const params = useParams();
  const campaignId = params.campaignId as string;

  const [events, setEvents] = useState<CalendarEventType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [isMyEventsOnly, setIsMyEventsOnly] = useState(false);

  // 데이터 로드
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        setError(null);

        // 월간 뷰 기준 전후 1개월 포함해서 가져오기
        const start = startOfMonth(subMonths(currentDate, 1));
        const end = endOfMonth(addMonths(currentDate, 1));

        const response = await api.get<CalendarEventType[]>(
          `/campaigns/${campaignId}/events?start=${start.toISOString()}&end=${end.toISOString()}`
        );
        setEvents(response || []);
      } catch (err) {
        console.error("Failed to load events:", err);
        setError(err instanceof Error ? err : new Error("일정 로드 실패"));
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [campaignId, currentDate]);

  // 이벤트 데이터 포맷 변환
  const formattedEvents = useMemo(() => {
    return events.map((event) => ({
      id: String(event.id),
      title: event.title,
      description: event.description,
      start_time: event.start_time,
      end_time: event.end_time,
      location: event.location,
      type: (event.type || "other") as
        | "meeting"
        | "campaign"
        | "deadline"
        | "briefing"
        | "other",
      is_all_day: event.is_all_day,
      attendees: event.attendees?.map((a) => ({
        id: String(a.id),
        name: a.full_name || a.email || "",
        avatar_url: a.avatar_url,
      })),
    }));
  }, [events]);

  // 선택된 날짜의 이벤트
  const selectedDayEvents = useMemo(() => {
    return formattedEvents.filter((event) =>
      isSameDay(new Date(event.start_time), selectedDate)
    );
  }, [formattedEvents, selectedDate]);

  // 네비게이션
  const handlePrevious = () => {
    setCurrentDate((prev) => subMonths(prev, 1));
  };

  const handleNext = () => {
    setCurrentDate((prev) => addMonths(prev, 1));
  };

  const handleToday = () => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDate(today);
  };

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
  };

  const handleEventClick = (eventId: string) => {
    // TODO: 이벤트 상세 다이얼로그 열기
    console.log("Event clicked:", eventId);
  };

  const handleAddEvent = () => {
    // TODO: 이벤트 생성 다이얼로그 열기
    console.log("Add event for date:", selectedDate);
  };

  if (loading && events.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingState text="캘린더를 불러오는 중..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">팀 캘린더</h1>
        <p className="text-muted-foreground">
          팀의 모든 일정을 확인하고 관리하세요
        </p>
      </div>

      {/* 캘린더 헤더 */}
      <CalendarHeader
        currentDate={currentDate}
        viewMode={viewMode}
        isMyEventsOnly={isMyEventsOnly}
        onPrevious={handlePrevious}
        onNext={handleNext}
        onToday={handleToday}
        onViewModeChange={setViewMode}
        onMyEventsToggle={setIsMyEventsOnly}
        onAddEvent={handleAddEvent}
      />

      {/* 캘린더 뷰 */}
      {viewMode === "month" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 캘린더 그리드 */}
          <div className="lg:col-span-2">
            <CalendarGrid
              currentDate={currentDate}
              selectedDate={selectedDate}
              events={formattedEvents}
              onDateSelect={handleDateSelect}
              onEventClick={handleEventClick}
            />
          </div>

          {/* 선택된 날짜 상세 */}
          <div className="lg:col-span-1">
            <EventDetailPanel
              date={selectedDate}
              events={selectedDayEvents}
              onEventClick={handleEventClick}
              onEventEdit={handleEventClick}
              onAddEvent={handleAddEvent}
            />
          </div>
        </div>
      )}

      {viewMode === "list" && (
        <EventListView
          events={formattedEvents}
          isLoading={loading}
          error={error}
          onEventClick={handleEventClick}
          onAddEvent={handleAddEvent}
        />
      )}

      {(viewMode === "week" || viewMode === "day") && (
        <div className="flex items-center justify-center h-64 border rounded-lg bg-muted/20">
          <p className="text-muted-foreground">
            {viewMode === "week" ? "주간" : "일간"} 뷰는 준비 중입니다
          </p>
        </div>
      )}
    </div>
  );
}
