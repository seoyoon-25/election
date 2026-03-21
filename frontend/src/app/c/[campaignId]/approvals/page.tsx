"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { ApprovalRequest, PaginatedResponse, ApprovalStatus } from "@/types";
import {
  Card,
  CardTitle,
  Button,
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
  useToast,
} from "@/components/ui";
import { StatusBadge, PermissionGate } from "@/components/common";
import { PERMISSIONS } from "@/lib/constants";
import { Check, X, Clock } from "lucide-react";
import { ko } from "date-fns/locale";
import { format } from "date-fns";

const STATUS_TABS: { status: ApprovalStatus | "all"; label: string }[] = [
  { status: "all", label: "전체" },
  { status: "pending", label: "대기중" },
  { status: "approved", label: "승인됨" },
  { status: "rejected", label: "반려됨" },
];

export default function ApprovalsPage() {
  const params = useParams();
  const campaignId = params.campaignId as string;
  const { toast } = useToast();

  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ApprovalStatus | "all">("pending");
  const [processingId, setProcessingId] = useState<number | null>(null);

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
        toast({
          variant: "destructive",
          title: "오류",
          description: "결재 목록을 불러오지 못했습니다.",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchApprovals();
  }, [campaignId, activeTab, toast]);

  const handleApprove = async (requestId: number) => {
    setProcessingId(requestId);
    try {
      await api.post(`/campaigns/${campaignId}/approvals/requests/${requestId}/decide`, {
        approved: true,
      });
      setRequests((prev) =>
        prev.map((r) =>
          r.id === requestId ? { ...r, status: "approved" as ApprovalStatus } : r
        )
      );
      toast({
        variant: "success",
        title: "승인 완료",
        description: "결재 요청이 승인되었습니다.",
      });
    } catch (err) {
      console.error("Failed to approve:", err);
      toast({
        variant: "destructive",
        title: "승인 실패",
        description: "결재 승인 처리 중 오류가 발생했습니다.",
      });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (requestId: number) => {
    setProcessingId(requestId);
    try {
      await api.post(`/campaigns/${campaignId}/approvals/requests/${requestId}/decide`, {
        approved: false,
      });
      setRequests((prev) =>
        prev.map((r) =>
          r.id === requestId ? { ...r, status: "rejected" as ApprovalStatus } : r
        )
      );
      toast({
        variant: "success",
        title: "반려 완료",
        description: "결재 요청이 반려되었습니다.",
      });
    } catch (err) {
      console.error("Failed to reject:", err);
      toast({
        variant: "destructive",
        title: "반려 실패",
        description: "결재 반려 처리 중 오류가 발생했습니다.",
      });
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">결재 현황</h1>
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
          <CardTitle>결재 요청 없음</CardTitle>
          <p className="text-gray-500 mt-2">
            {activeTab === "pending"
              ? "현재 대기 중인 결재가 없습니다"
              : "결재 요청이 없습니다"}
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {requests.map((request) => (
            <Card key={request.id} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-medium text-gray-900">
                      {request.entity_type} #{request.entity_id}
                    </h3>
                    <StatusBadge status={request.status} />
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {format(new Date(request.created_at), "yyyy년 M월 d일 HH:mm", { locale: ko })} 요청
                  </p>
                </div>

                {request.status === "pending" && (
                  <PermissionGate permission={PERMISSIONS.APPROVAL_DECIDE}>
                    <div className="flex items-center gap-2">
                      {/* 반려 확인 다이얼로그 */}
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="secondary"
                            size="sm"
                            disabled={processingId === request.id}
                          >
                            <X className="h-4 w-4 mr-1" />
                            반려
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>결재 반려</AlertDialogTitle>
                            <AlertDialogDescription>
                              이 결재 요청을 반려하시겠습니까? 이 작업은 취소할 수 없습니다.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>취소</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleReject(request.id)}
                              className="bg-red-600 hover:bg-red-700"
                            >
                              반려
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>

                      {/* 승인 확인 다이얼로그 */}
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            size="sm"
                            disabled={processingId === request.id}
                          >
                            <Check className="h-4 w-4 mr-1" />
                            승인
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>결재 승인</AlertDialogTitle>
                            <AlertDialogDescription>
                              이 결재 요청을 승인하시겠습니까?
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>취소</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleApprove(request.id)}
                            >
                              승인
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </PermissionGate>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
