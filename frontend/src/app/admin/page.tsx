"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Building2, Users, Mail, TrendingUp, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { AdminStats } from "@/types";
import { Card, CardHeader, CardTitle, CardContent, Skeleton } from "@/components/ui";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await api.get<AdminStats>("/admin/stats");
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "통계를 불러올 수 없습니다");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-5 w-72" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {error}
      </div>
    );
  }

  const statCards = [
    {
      title: "전체 캠프",
      value: stats?.total_campaigns ?? 0,
      subValue: `활성: ${stats?.active_campaigns ?? 0}`,
      icon: Building2,
      href: "/admin/campaigns",
      color: "bg-blue-500",
    },
    {
      title: "전체 사용자",
      value: stats?.total_users ?? 0,
      subValue: `활성: ${stats?.active_users ?? 0}`,
      icon: Users,
      href: "/admin/users",
      color: "bg-green-500",
    },
    {
      title: "초대",
      value: stats?.total_invitations ?? 0,
      subValue: `대기: ${stats?.pending_invitations ?? 0}`,
      icon: Mail,
      href: "/admin/invitations",
      color: "bg-yellow-500",
    },
    {
      title: "오늘 가입",
      value: stats?.today_signups ?? 0,
      subValue: `새 캠프: ${stats?.today_campaigns ?? 0}`,
      icon: TrendingUp,
      color: "bg-purple-500",
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">관리자 대시보드</h1>
        <p className="text-gray-600 mt-1">플랫폼 전체 현황을 확인하세요</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <Card key={stat.title} className="relative overflow-hidden">
            {stat.href ? (
              <Link href={stat.href} className="block">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-500">{stat.title}</p>
                      <p className="text-3xl font-bold text-gray-900 mt-2">
                        {stat.value.toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">{stat.subValue}</p>
                    </div>
                    <div className={`p-3 rounded-lg ${stat.color}`}>
                      <stat.icon className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100">
                    <div
                      className={`h-full ${stat.color}`}
                      style={{
                        width: `${Math.min(100, (stat.value / (stats?.total_campaigns || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                </CardContent>
              </Link>
            ) : (
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">{stat.title}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                      {stat.value.toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">{stat.subValue}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.color}`}>
                    <stat.icon className="h-6 w-6 text-white" />
                  </div>
                </div>
              </CardContent>
            )}
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>빠른 작업</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Link
              href="/admin/campaigns"
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Building2 className="h-5 w-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">캠프 관리</span>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              href="/admin/users"
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">사용자 관리</span>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </Link>
            <Link
              href="/admin/invitations"
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">초대 관리</span>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>플랫폼 요약</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">캠프 활성화율</span>
                <span className="text-sm font-medium text-gray-900">
                  {stats && stats.total_campaigns > 0
                    ? Math.round((stats.active_campaigns / stats.total_campaigns) * 100)
                    : 0}
                  %
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full"
                  style={{
                    width: `${
                      stats && stats.total_campaigns > 0
                        ? (stats.active_campaigns / stats.total_campaigns) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>

              <div className="flex justify-between items-center pt-4">
                <span className="text-sm text-gray-600">사용자 활성화율</span>
                <span className="text-sm font-medium text-gray-900">
                  {stats && stats.total_users > 0
                    ? Math.round((stats.active_users / stats.total_users) * 100)
                    : 0}
                  %
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{
                    width: `${
                      stats && stats.total_users > 0
                        ? (stats.active_users / stats.total_users) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>

              <div className="flex justify-between items-center pt-4">
                <span className="text-sm text-gray-600">초대 대기율</span>
                <span className="text-sm font-medium text-gray-900">
                  {stats && stats.total_invitations > 0
                    ? Math.round((stats.pending_invitations / stats.total_invitations) * 100)
                    : 0}
                  %
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-yellow-500 h-2 rounded-full"
                  style={{
                    width: `${
                      stats && stats.total_invitations > 0
                        ? (stats.pending_invitations / stats.total_invitations) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
