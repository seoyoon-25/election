"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Task, CalendarEvent, ApprovalRequest, PaginatedResponse } from "@/types";
import {
  AlertBanner,
  MyTasksWidget,
  TodayScheduleWidget,
  PendingApprovalsWidget,
  TeamProgressWidget,
  AnnouncementWidget,
} from "@/components/dashboard";
import { getDueStatus } from "@/lib/utils";

interface Announcement {
  id: string;
  title: string;
  created_at: string;
  is_pinned?: boolean;
  is_important?: boolean;
}

export default function DashboardPage() {
  const params = useParams();
  const campaignId = params.campaignId as string;

  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 오늘 날짜 범위 계산
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        const [tasksRes, eventsRes, approvalsRes] = await Promise.all([
          // 내 태스크 (마감일순, 완료되지 않은 것)
          api.get<PaginatedResponse<Task>>(
            `/campaigns/${campaignId}/tasks?page_size=10&sort=due_date&status_not=done`
          ).catch(() => ({ items: [] })),
          // 오늘 일정
          api.get<CalendarEvent[]>(
            `/campaigns/${campaignId}/events?start=${today.toISOString()}&end=${tomorrow.toISOString()}`
          ).catch(() => []),
          // 결재 대기
          api.get<PaginatedResponse<ApprovalRequest>>(
            `/campaigns/${campaignId}/approvals/requests?status=pending&page_size=10`
          ).catch(() => ({ items: [] })),
        ]);

        setTasks(tasksRes.items || []);
        setEvents(eventsRes || []);
        setApprovals(approvalsRes.items || []);

        // 공지사항 (별도 처리 - 실패해도 무시)
        try {
          const announcementsRes = await api.get<Announcement[]>(
            `/campaigns/${campaignId}/announcements?page_size=5`
          );
          setAnnouncements(announcementsRes || []);
        } catch {
          setAnnouncements([]);
        }
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
        setError(err instanceof Error ? err : new Error("데이터 로드 실패"));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [campaignId]);

  // 알림 데이터 계산
  const alerts = [];
  const overdueCount = tasks.filter(
    (t) => getDueStatus(t.due_date) === "overdue"
  ).length;
  const todayDueCount = tasks.filter(
    (t) => getDueStatus(t.due_date) === "today"
  ).length;
  const pendingApprovalsCount = approvals.filter(
    (a) => a.status === "pending"
  ).length;

  if (overdueCount > 0) {
    alerts.push({
      type: "overdue" as const,
      count: overdueCount,
      message: "지연된 태스크",
      href: `/c/${campaignId}/my-tasks?filter=overdue`,
    });
  }
  if (pendingApprovalsCount > 0) {
    alerts.push({
      type: "urgent_approval" as const,
      count: pendingApprovalsCount,
      message: "결재 대기",
      href: `/c/${campaignId}/my-approvals`,
    });
  }
  if (todayDueCount > 0) {
    alerts.push({
      type: "deadline" as const,
      count: todayDueCount,
      message: "오늘 마감",
      href: `/c/${campaignId}/my-tasks?filter=today`,
    });
  }
  if (events.length > 0) {
    alerts.push({
      type: "meeting" as const,
      count: events.length,
      message: "오늘 일정",
      href: `/c/${campaignId}/my-calendar`,
    });
  }

  // 팀별 진행 현황 (샘플 데이터 - 실제로는 API에서 가져와야 함)
  const teamStats = [
    { teamName: "총무팀", total: 12, completed: 8, delayed: 1 },
    { teamName: "정책팀", total: 8, completed: 3, delayed: 2 },
    { teamName: "미디어팀", total: 15, completed: 10, delayed: 0 },
  ];

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">대시보드</h1>
        <p className="text-muted-foreground">
          오늘 해야 할 일을 한눈에 확인하세요
        </p>
      </div>

      {/* 긴급 알림 배너 */}
      {alerts.length > 0 && <AlertBanner alerts={alerts} />}

      {/* 메인 콘텐츠 그리드 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 좌측: 내 태스크 */}
        <MyTasksWidget
          tasks={tasks.map((t) => ({
            id: String(t.id),
            title: t.title,
            status: t.status as any,
            priority: t.priority as any,
            due_date: t.due_date,
          }))}
          isLoading={loading}
          error={error}
          campaignId={campaignId}
        />

        {/* 우측: 오늘 일정 */}
        <TodayScheduleWidget
          events={events.map((e) => ({
            id: String(e.id),
            title: e.title,
            start_time: e.start_time,
            end_time: e.end_time,
            location: e.location,
            is_all_day: e.is_all_day,
          }))}
          isLoading={loading}
          error={error}
          campaignId={campaignId}
        />
      </div>

      {/* 하단 그리드: 결재 + 공지 + 팀 현황 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 결재 대기함 */}
        <PendingApprovalsWidget
          approvals={approvals.map((a) => ({
            id: String(a.id),
            entity_type: a.entity_type,
            entity_id: String(a.entity_id),
            status: a.status as any,
            created_at: a.created_at,
            requested_by: a.requested_by
              ? { name: a.requested_by.full_name || "알 수 없음" }
              : undefined,
          }))}
          isLoading={loading}
          error={error}
          campaignId={campaignId}
          onApprove={async (id) => {
            try {
              await api.post(`/campaigns/${campaignId}/approvals/requests/${id}/decide`, {
                decision: "approved",
              });
              setApprovals((prev) =>
                prev.map((a) =>
                  String(a.id) === id ? { ...a, status: "approved" } : a
                )
              );
            } catch (err) {
              console.error("Failed to approve:", err);
            }
          }}
          onReject={async (id) => {
            try {
              await api.post(`/campaigns/${campaignId}/approvals/requests/${id}/decide`, {
                decision: "rejected",
              });
              setApprovals((prev) =>
                prev.map((a) =>
                  String(a.id) === id ? { ...a, status: "rejected" } : a
                )
              );
            } catch (err) {
              console.error("Failed to reject:", err);
            }
          }}
        />

        {/* 공지사항 */}
        <AnnouncementWidget
          announcements={announcements}
          isLoading={loading}
          campaignId={campaignId}
        />

        {/* 팀별 진행 현황 */}
        <TeamProgressWidget teamStats={teamStats} isLoading={loading} />
      </div>
    </div>
  );
}
