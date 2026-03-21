"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyCampaigns, isAuthenticated } from "@/lib/auth";
import { CampaignWithRole } from "@/types";
import { Card, CardTitle, Badge, Button } from "@/components/ui";
import { Header } from "@/components/layout";
import { ChevronRight, Building2, Plus, Mail } from "lucide-react";

export default function CampaignsPage() {
  const router = useRouter();
  const [campaigns, setCampaigns] = useState<CampaignWithRole[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const fetchCampaigns = async () => {
      try {
        const data = await getMyCampaigns();
        setCampaigns(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load campaigns");
      } finally {
        setLoading(false);
      }
    };

    fetchCampaigns();
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-4xl mx-auto py-8 px-4">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">내 캠프</h1>
            <p className="text-gray-600 mt-1">관리할 캠프를 선택하세요</p>
          </div>
          <Link href="/campaigns/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              새 캠프 만들기
            </Button>
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {campaigns.length === 0 ? (
          <Card className="p-8 text-center py-12">
            <Building2 className="h-16 w-16 text-gray-300 mx-auto mb-6" />
            <CardTitle className="text-xl">참여 중인 캠프가 없습니다</CardTitle>
            <p className="text-gray-600 mt-3 mb-8 max-w-md mx-auto">
              새 캠프를 만들어 선거 운동을 시작하거나,<br />
              다른 캠프의 초대를 기다리세요.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/campaigns/new">
                <Button size="lg">
                  <Plus className="w-5 h-5 mr-2" />
                  캠프 만들기
                </Button>
              </Link>
            </div>
            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                <Mail className="w-4 h-4" />
                <span>초대 이메일을 받으셨나요? 이메일의 링크를 클릭하세요</span>
              </div>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {campaigns.map((campaign) => (
              <Link
                key={campaign.id}
                href={`/c/${campaign.id}/dashboard`}
              >
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center">
                        <Building2 className="h-6 w-6 text-primary-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {campaign.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="blue">{campaign.role_name}</Badge>
                          {campaign.status !== "active" && (
                            <Badge variant="gray">{campaign.status}</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
