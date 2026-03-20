"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  XCircle,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { AdminInvitation, PaginatedResponse } from "@/types";
import {
  Card,
  CardContent,
  Badge,
  Button,
  Input,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Skeleton,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui";

const statusOptions = [
  { value: "", label: "전체 상태" },
  { value: "pending", label: "대기중" },
  { value: "accepted", label: "수락됨" },
  { value: "expired", label: "만료됨" },
  { value: "cancelled", label: "취소됨" },
];

const statusLabels: Record<string, string> = {
  pending: "대기중",
  accepted: "수락됨",
  expired: "만료됨",
  cancelled: "취소됨",
};

const statusColors: Record<string, "yellow" | "green" | "gray" | "red"> = {
  pending: "yellow",
  accepted: "green",
  expired: "gray",
  cancelled: "red",
};

const statusIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  pending: Clock,
  accepted: CheckCircle,
  expired: AlertCircle,
  cancelled: XCircle,
};

export default function AdminInvitationsPage() {
  const [invitations, setInvitations] = useState<AdminInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");

  // Resend dialog
  const [resendInvitation, setResendInvitation] = useState<AdminInvitation | null>(null);
  const [resendDialogOpen, setResendDialogOpen] = useState(false);
  const [resending, setResending] = useState(false);

  // Cancel dialog
  const [cancelInvitation, setCancelInvitation] = useState<AdminInvitation | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const fetchInvitations = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20",
      });
      if (search) params.append("search", search);
      if (statusFilter) params.append("status", statusFilter);

      const data = await api.get<PaginatedResponse<AdminInvitation>>(
        `/admin/invitations?${params.toString()}`
      );
      setInvitations(data.items);
      setTotalPages(data.pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "초대 목록을 불러올 수 없습니다");
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    fetchInvitations();
  }, [fetchInvitations]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleResend = (invitation: AdminInvitation) => {
    setResendInvitation(invitation);
    setResendDialogOpen(true);
  };

  const confirmResend = async () => {
    if (!resendInvitation) return;

    setResending(true);
    try {
      await api.post(`/admin/invitations/${resendInvitation.id}/resend`);
      setResendDialogOpen(false);
      fetchInvitations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "재발송에 실패했습니다");
    } finally {
      setResending(false);
    }
  };

  const handleCancel = (invitation: AdminInvitation) => {
    setCancelInvitation(invitation);
    setCancelDialogOpen(true);
  };

  const confirmCancel = async () => {
    if (!cancelInvitation) return;

    setCancelling(true);
    try {
      await api.delete(`/admin/invitations/${cancelInvitation.id}`);
      setCancelDialogOpen(false);
      fetchInvitations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "취소에 실패했습니다");
    } finally {
      setCancelling(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const isExpiringSoon = (expiresAt: string) => {
    const expiry = new Date(expiresAt);
    const now = new Date();
    const hoursUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60);
    return hoursUntilExpiry > 0 && hoursUntilExpiry < 24;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">초대 관리</h1>
        <p className="text-gray-600 mt-1">모든 캠프 초대를 관리합니다</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
          <button
            className="float-right font-bold"
            onClick={() => setError("")}
          >
            &times;
          </button>
        </div>
      )}

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
            <form onSubmit={handleSearch} className="flex gap-2 flex-1 max-w-md">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="이메일로 검색..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" variant="secondary">
                검색
              </Button>
            </form>

            <div className="flex gap-2 items-center">
              <Select value={statusFilter} onValueChange={(value) => {
                setStatusFilter(value);
                setPage(1);
              }}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="전체 상태" />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : invitations.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              초대가 없습니다
            </div>
          ) : (
            <TooltipProvider>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>이메일</TableHead>
                    <TableHead>캠프</TableHead>
                    <TableHead>역할</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>초대자</TableHead>
                    <TableHead>만료일</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invitations.map((invitation) => {
                    const StatusIcon = statusIcons[invitation.status] || Clock;
                    return (
                      <TableRow key={invitation.id}>
                        <TableCell className="font-medium">
                          {invitation.email}
                        </TableCell>
                        <TableCell>{invitation.campaign_name}</TableCell>
                        <TableCell>
                          <div>
                            {invitation.role_name || "-"}
                            {invitation.department_name && (
                              <span className="text-xs text-gray-500 block">
                                {invitation.department_name}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={statusColors[invitation.status] || "gray"}
                            className="flex items-center gap-1 w-fit"
                          >
                            <StatusIcon className="h-3 w-3" />
                            {statusLabels[invitation.status] || invitation.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {invitation.invited_by_name ? (
                            <Tooltip>
                              <TooltipTrigger className="text-left">
                                <span className="text-sm">
                                  {invitation.invited_by_name}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent>
                                {invitation.invited_by_email}
                              </TooltipContent>
                            </Tooltip>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {formatDate(invitation.expires_at)}
                            {invitation.status === "pending" &&
                              isExpiringSoon(invitation.expires_at) && (
                                <span className="text-orange-500 text-xs block">
                                  곧 만료
                                </span>
                              )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {invitation.status === "pending" && (
                            <div className="flex gap-1">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleResend(invitation)}
                                  >
                                    <RefreshCw className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>재발송</TooltipContent>
                              </Tooltip>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleCancel(invitation)}
                                  >
                                    <XCircle className="h-4 w-4 text-red-500" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>취소</TooltipContent>
                              </Tooltip>
                            </div>
                          )}
                          {invitation.status === "expired" && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleResend(invitation)}
                                >
                                  <RefreshCw className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>재발송</TooltipContent>
                            </Tooltip>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TooltipProvider>
          )}

          {/* Pagination */}
          {!loading && invitations.length > 0 && (
            <div className="flex items-center justify-between px-6 py-4 border-t">
              <div className="text-sm text-gray-500">
                총 {total.toLocaleString()}개 중 {(page - 1) * 20 + 1}-
                {Math.min(page * 20, total)}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-gray-600">
                  {page} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resend Dialog */}
      <Dialog open={resendDialogOpen} onOpenChange={setResendDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>초대 재발송</DialogTitle>
            <DialogDescription>
              {resendInvitation && (
                <>
                  <strong>{resendInvitation.email}</strong>에게 초대를 다시 발송합니다.
                  <br />
                  만료일이 7일 후로 갱신됩니다.
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setResendDialogOpen(false)}
              disabled={resending}
            >
              취소
            </Button>
            <Button onClick={confirmResend} loading={resending}>
              재발송
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>초대 취소</DialogTitle>
            <DialogDescription>
              {cancelInvitation && (
                <>
                  <strong>{cancelInvitation.email}</strong>의 초대를 취소합니다.
                  <br />
                  이 작업은 되돌릴 수 없습니다.
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCancelDialogOpen(false)}
              disabled={cancelling}
            >
              닫기
            </Button>
            <Button
              variant="destructive"
              onClick={confirmCancel}
              loading={cancelling}
            >
              취소
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
