"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { CampaignMembership } from "@/types";
import { Card, CardTitle, Badge, Button } from "@/components/ui";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui";
import { UserPlus, Users, Mail } from "lucide-react";
import { ErrorState, PermissionGate } from "@/components/common";
import { PERMISSIONS } from "@/lib/constants";

interface MemberWithUser extends CampaignMembership {
  user: {
    id: number;
    email: string;
    full_name: string;
  };
}

export default function MembersPage() {
  const params = useParams();
  const campaignId = params.campaignId as string;

  const [members, setMembers] = useState<MemberWithUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMembers = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await api.get<MemberWithUser[]>(
        `/campaigns/${campaignId}/members`
      );
      setMembers(response || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "멤버 목록을 불러올 수 없습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [campaignId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">팀 멤버</h1>
        <ErrorState
          title="멤버 로드 실패"
          message={error}
          onRetry={fetchMembers}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">팀 멤버</h1>
        <PermissionGate permission={PERMISSIONS.CAMPAIGN_MANAGE_MEMBERS}>
          <Button>
            <UserPlus className="h-4 w-4 mr-1" />
            멤버 초대
          </Button>
        </PermissionGate>
      </div>

      {members.length === 0 ? (
        <Card className="text-center py-12">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <CardTitle>팀 멤버가 없습니다</CardTitle>
          <p className="text-gray-500 mt-2">
            캠프에 참여할 멤버를 초대하세요
          </p>
        </Card>
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <Table className="min-w-[600px]">
              <TableHeader>
                <TableRow>
                  <TableHead>멤버</TableHead>
                  <TableHead>역할</TableHead>
                  <TableHead>이메일</TableHead>
                  <PermissionGate permission={PERMISSIONS.CAMPAIGN_MANAGE_MEMBERS}>
                    <TableHead>관리</TableHead>
                  </PermissionGate>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center mr-3">
                          <span className="text-primary-700 font-medium">
                            {member.user.full_name
                              .split(" ")
                              .map((n) => n[0])
                              .join("")
                              .toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">
                            {member.user.full_name}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="blue">{member.role.name}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center text-gray-500">
                        <Mail className="h-4 w-4 mr-2" />
                        {member.user.email}
                      </div>
                    </TableCell>
                    <PermissionGate permission={PERMISSIONS.CAMPAIGN_MANAGE_MEMBERS}>
                      <TableCell>
                        <Button variant="secondary" size="sm">
                          역할 변경
                        </Button>
                      </TableCell>
                    </PermissionGate>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}
    </div>
  );
}
