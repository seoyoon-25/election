"use client";

import { useState, useEffect, ReactNode } from "react";
import { useRouter, useParams } from "next/navigation";
import { isAuthenticated, getCurrentUser, logout } from "@/lib/auth";
import { api } from "@/lib/api";
import { Campaign, User, MembershipWithRole } from "@/types";
import { GlobalHeader, Sidebar } from "@/components/layout";
import { TooltipProvider } from "@/components/ui/tooltip";
import { PermissionProvider } from "@/contexts/PermissionContext";

interface CampaignLayoutProps {
  children: ReactNode;
}

export default function CampaignLayout({ children }: CampaignLayoutProps) {
  const router = useRouter();
  const params = useParams();
  const campaignId = params.campaignId as string;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [membership, setMembership] = useState<MembershipWithRole | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingApprovals, setPendingApprovals] = useState(0);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const fetchData = async () => {
      try {
        const campaignHeaders = { "X-Campaign-ID": campaignId };

        const [campaignData, userData] = await Promise.all([
          api.get<Campaign>(`/campaigns/${campaignId}`, { headers: campaignHeaders }),
          getCurrentUser(),
        ]);
        setCampaign(campaignData);
        setUser(userData);

        // 사용자의 캠페인 멤버십/권한 정보 조회
        try {
          const membershipRes = await api.get<MembershipWithRole>(
            `/members/me`,
            { headers: campaignHeaders }
          );
          setMembership(membershipRes);
        } catch {
          // 멤버십 조회 실패 시 기본값 사용
        }

        // 결재 대기 건수 조회
        try {
          const approvalsRes = await api.get<{ total: number }>(
            `/approvals/requests?status=pending&page_size=1`,
            { headers: campaignHeaders }
          );
          setPendingApprovals(approvalsRes.total || 0);
        } catch {
          // 결재 조회 실패 시 무시
        }
      } catch (err) {
        console.error("Failed to load campaign:", err);
        router.push("/campaigns");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [campaignId, router]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <PermissionProvider
        permissions={membership?.role.permissions || []}
        roleName={membership?.role.name || "member"}
        roleSlug={membership?.role.slug || "member"}
        isOwner={membership?.is_owner || false}
        isAdmin={membership?.is_admin || false}
        isDepartmentHead={membership?.is_department_head || false}
      >
        <div className="min-h-screen bg-background">
          {/* 글로벌 상단바 */}
          <GlobalHeader
            user={{
              id: String(user?.id || ""),
              name: user?.full_name || "사용자",
              email: user?.email || "",
              avatar_url: user?.avatar_url,
            }}
            campaignId={campaignId}
            campaignName={campaign?.name || "캠페인"}
            notificationCount={pendingApprovals}
            onLogout={handleLogout}
          />

          <div className="flex h-[calc(100vh-3.5rem)]">
            {/* 사이드바 */}
            <Sidebar
              campaignId={campaignId}
              pendingApprovals={pendingApprovals}
            />

            {/* 메인 콘텐츠 */}
            <main className="flex-1 overflow-auto">
              <div className="container max-w-7xl mx-auto p-6">
                {children}
              </div>
            </main>
          </div>
        </div>
      </PermissionProvider>
    </TooltipProvider>
  );
}
