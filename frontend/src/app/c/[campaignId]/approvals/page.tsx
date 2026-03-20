"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ApprovalRequest, PaginatedResponse, ApprovalStatus } from "@/types";
import { Card, CardTitle, Button } from "@/components/ui";
import { StatusBadge } from "@/components/common";
import { Check, X, Clock } from "lucide-react";
import { format } from "date-fns";

const STATUS_TABS: { status: ApprovalStatus | "all"; label: string }[] = [
  { status: "all", label: "All" },
  { status: "pending", label: "Pending" },
  { status: "approved", label: "Approved" },
  { status: "rejected", label: "Rejected" },
];

export default function ApprovalsPage() {
  const params = useParams();
  const campaignId = params.campaignId as string;

  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ApprovalStatus | "all">("pending");

  useEffect(() => {
    const fetchApprovals = async () => {
      setLoading(true);
      try {
        const statusQuery = activeTab === "all" ? "" : `&status=${activeTab}`;
        const response = await api.get<PaginatedResponse<ApprovalRequest>>(
          `/campaigns/${campaignId}/approvals/requests?page_size=50${statusQuery}`
        );
        setRequests(response.items || []);
      } catch (err) {
        console.error("Failed to load approvals:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchApprovals();
  }, [campaignId, activeTab]);

  const handleApprove = async (requestId: number) => {
    try {
      await api.post(`/campaigns/${campaignId}/approvals/requests/${requestId}/decide`, {
        approved: true,
      });
      setRequests((prev) =>
        prev.map((r) =>
          r.id === requestId ? { ...r, status: "approved" as ApprovalStatus } : r
        )
      );
    } catch (err) {
      console.error("Failed to approve:", err);
    }
  };

  const handleReject = async (requestId: number) => {
    try {
      await api.post(`/campaigns/${campaignId}/approvals/requests/${requestId}/decide`, {
        approved: false,
      });
      setRequests((prev) =>
        prev.map((r) =>
          r.id === requestId ? { ...r, status: "rejected" as ApprovalStatus } : r
        )
      );
    } catch (err) {
      console.error("Failed to reject:", err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Approvals</h1>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.status}
              onClick={() => setActiveTab(tab.status)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === tab.status
                    ? "border-primary-600 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : requests.length === 0 ? (
        <Card className="text-center py-12">
          <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <CardTitle>No approval requests</CardTitle>
          <p className="text-gray-500 mt-2">
            {activeTab === "pending"
              ? "No pending approvals at this time"
              : "No approval requests found"}
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {requests.map((request) => (
            <Card key={request.id}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-medium text-gray-900">
                      {request.entity_type} #{request.entity_id}
                    </h3>
                    <StatusBadge status={request.status} />
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Requested {format(new Date(request.created_at), "MMM d, yyyy 'at' h:mm a")}
                  </p>
                </div>

                {request.status === "pending" && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleReject(request.id)}
                    >
                      <X className="h-4 w-4 mr-1" />
                      Reject
                    </Button>
                    <Button size="sm" onClick={() => handleApprove(request.id)}>
                      <Check className="h-4 w-4 mr-1" />
                      Approve
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
