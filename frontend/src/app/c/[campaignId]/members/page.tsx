"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { CampaignMembership } from "@/types";
import { Card, CardTitle, Badge, Button } from "@/components/ui";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui";
import { UserPlus, Users, Mail } from "lucide-react";
import { format } from "date-fns";

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

  useEffect(() => {
    const fetchMembers = async () => {
      try {
        const response = await api.get<MemberWithUser[]>(
          `/campaigns/${campaignId}/members`
        );
        setMembers(response || []);
      } catch (err) {
        console.error("Failed to load members:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMembers();
  }, [campaignId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Team Members</h1>
        <Button>
          <UserPlus className="h-4 w-4 mr-1" />
          Invite Member
        </Button>
      </div>

      {members.length === 0 ? (
        <Card className="text-center py-12">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <CardTitle>No team members</CardTitle>
          <p className="text-gray-500 mt-2">
            Invite members to join your campaign
          </p>
        </Card>
      ) : (
        <Card padding="none">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Member</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Actions</TableHead>
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
                  <TableCell>
                    <Button variant="secondary" size="sm">
                      Edit Role
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
