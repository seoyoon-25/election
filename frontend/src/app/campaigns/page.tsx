"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyCampaigns, isAuthenticated } from "@/lib/auth";
import { CampaignMembership } from "@/types";
import { Card, CardTitle, Badge, Button } from "@/components/ui";
import { Header } from "@/components/layout";
import { ChevronRight, Building2 } from "lucide-react";

export default function CampaignsPage() {
  const router = useRouter();
  const [memberships, setMemberships] = useState<CampaignMembership[]>([]);
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
        setMemberships(data);
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
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">내 캠프</h1>
          <p className="text-gray-600 mt-1">관리할 캠프를 선택하세요</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {memberships.length === 0 ? (
          <Card padding="lg" className="text-center">
            <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <CardTitle>캠프가 없습니다</CardTitle>
            <p className="text-gray-600 mt-2">
              아직 참여 중인 캠프가 없습니다.
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {memberships.map((membership) => (
              <Link
                key={membership.id}
                href={`/c/${membership.campaign_id}/dashboard`}
              >
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center">
                        <Building2 className="h-6 w-6 text-primary-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {membership.campaign.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="blue">{membership.role.name}</Badge>
                          {!membership.campaign.is_active && (
                            <Badge variant="gray">Inactive</Badge>
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
