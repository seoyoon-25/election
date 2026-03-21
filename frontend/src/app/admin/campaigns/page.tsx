"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, Download, ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";
import { api } from "@/lib/api";
import { AdminCampaign, PaginatedResponse } from "@/types";
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
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui";

const statusOptions = [
  { value: "all", label: "전체 상태" },
  { value: "draft", label: "준비중" },
  { value: "active", label: "활성" },
  { value: "paused", label: "일시정지" },
  { value: "completed", label: "완료" },
  { value: "archived", label: "보관" },
];

const permissionOptions = [
  { value: "all", label: "전체 권한" },
  { value: "pending", label: "승인대기" },
  { value: "active", label: "활동중" },
  { value: "ended", label: "종료" },
];

// 권한 값에 해당하는 상태 목록
const permissionToStatuses: Record<string, string[]> = {
  pending: ["draft"],
  active: ["active", "paused"],
  ended: ["completed", "archived"],
};

// 권한 변경 시 사용할 기본 상태값
const permissionToDefaultStatus: Record<string, string> = {
  pending: "draft",
  active: "active",
  ended: "completed",
};

// 권한 변경 옵션 (필터에서 "all" 제외)
const permissionChangeOptions = permissionOptions.filter(p => p.value !== "all");

const statusLabels: Record<string, string> = {
  draft: "준비중",
  active: "활성",
  paused: "일시정지",
  completed: "완료",
  archived: "보관",
};

const statusColors: Record<string, "green" | "gray" | "yellow" | "blue" | "red"> = {
  draft: "gray",
  active: "green",
  paused: "yellow",
  completed: "blue",
  archived: "gray",
};

// 권한 상태 매핑 (승인대기, 활동중, 종료)
const getPermissionStatus = (status: string): { label: string; color: "yellow" | "green" | "gray" } => {
  switch (status) {
    case "draft":
      return { label: "승인대기", color: "yellow" };
    case "active":
    case "paused":
      return { label: "활동중", color: "green" };
    case "completed":
    case "archived":
      return { label: "종료", color: "gray" };
    default:
      return { label: "승인대기", color: "yellow" };
  }
};

export default function AdminCampaignsPage() {
  const [campaigns, setCampaigns] = useState<AdminCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [permissionFilter, setPermissionFilter] = useState("all");
  const [searchInput, setSearchInput] = useState("");

  // Status change dialog
  const [selectedCampaign, setSelectedCampaign] = useState<AdminCampaign | null>(null);
  const [newStatus, setNewStatus] = useState("");
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [updating, setUpdating] = useState(false);

  // Permission change dialog
  const [newPermission, setNewPermission] = useState("");
  const [permissionDialogOpen, setPermissionDialogOpen] = useState(false);

  const fetchCampaigns = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20",
      });
      if (search) params.append("search", search);

      // 권한 필터가 설정된 경우 해당하는 상태들로 필터링
      if (permissionFilter && permissionFilter !== "all") {
        const statuses = permissionToStatuses[permissionFilter];
        if (statuses) {
          statuses.forEach(s => params.append("status", s));
        }
      } else if (statusFilter && statusFilter !== "all") {
        params.append("status", statusFilter);
      }

      const data = await api.get<PaginatedResponse<AdminCampaign>>(
        `/admin/campaigns?${params.toString()}`
      );
      setCampaigns(data.items);
      setTotalPages(data.pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "캠프 목록을 불러올 수 없습니다");
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter, permissionFilter]);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleStatusChange = (campaign: AdminCampaign, status: string) => {
    setSelectedCampaign(campaign);
    setNewStatus(status);
    setStatusDialogOpen(true);
  };

  const confirmStatusChange = async () => {
    if (!selectedCampaign || !newStatus) return;

    setUpdating(true);
    try {
      await api.patch(`/admin/campaigns/${selectedCampaign.id}`, {
        status: newStatus,
      });
      setStatusDialogOpen(false);
      fetchCampaigns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "상태 변경에 실패했습니다");
    } finally {
      setUpdating(false);
    }
  };

  const handlePermissionChange = (campaign: AdminCampaign, permission: string) => {
    setSelectedCampaign(campaign);
    setNewPermission(permission);
    setPermissionDialogOpen(true);
  };

  const confirmPermissionChange = async () => {
    if (!selectedCampaign || !newPermission) return;

    const targetStatus = permissionToDefaultStatus[newPermission];
    if (!targetStatus) return;

    setUpdating(true);
    try {
      await api.patch(`/admin/campaigns/${selectedCampaign.id}`, {
        status: targetStatus,
      });
      setPermissionDialogOpen(false);
      fetchCampaigns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "권한 변경에 실패했습니다");
    } finally {
      setUpdating(false);
    }
  };

  // 현재 캠페인의 권한 값 가져오기
  const getCurrentPermission = (status: string): string => {
    if (permissionToStatuses.pending.includes(status)) return "pending";
    if (permissionToStatuses.active.includes(status)) return "active";
    if (permissionToStatuses.ended.includes(status)) return "ended";
    return "pending";
  };

  const handleExportCSV = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/campaigns/export`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        }
      );
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "campaigns.csv";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "내보내기 실패");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">캠프 관리</h1>
        <p className="text-gray-600 mt-1">모든 캠프를 관리합니다</p>
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
                  placeholder="이름, 슬러그로 검색..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" variant="secondary">
                검색
              </Button>
            </form>

            <div className="flex gap-2 items-center flex-wrap">
              <Select value={permissionFilter} onValueChange={(value) => {
                setPermissionFilter(value);
                if (value !== "all") setStatusFilter("all");
                setPage(1);
              }}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="전체 권한" />
                </SelectTrigger>
                <SelectContent>
                  {permissionOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={statusFilter} onValueChange={(value) => {
                setStatusFilter(value);
                if (value !== "all") setPermissionFilter("all");
                setPage(1);
              }}>
                <SelectTrigger className="w-[130px]">
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

              <Button variant="outline" onClick={handleExportCSV}>
                <Download className="h-4 w-4 mr-2" />
                CSV
              </Button>
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
          ) : campaigns.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              캠프가 없습니다
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>이름</TableHead>
                    <TableHead>슬러그</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>멤버</TableHead>
                    <TableHead>대표</TableHead>
                    <TableHead>생성일</TableHead>
                    <TableHead>권한</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaigns.map((campaign) => (
                    <TableRow key={campaign.id}>
                      <TableCell className="font-mono text-sm">
                        {campaign.id}
                      </TableCell>
                      <TableCell className="font-medium">
                        {campaign.name}
                      </TableCell>
                      <TableCell className="text-gray-500 font-mono text-sm">
                        {campaign.slug}
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusColors[campaign.status] || "gray"}>
                          {statusLabels[campaign.status] || campaign.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{campaign.member_count}</TableCell>
                      <TableCell>
                        {campaign.owner_name ? (
                          <div>
                            <div className="font-medium">{campaign.owner_name}</div>
                            <div className="text-xs text-gray-500">
                              {campaign.owner_email}
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-gray-500">
                        {formatDate(campaign.created_at)}
                      </TableCell>
                      <TableCell>
                        {(() => {
                          const permission = getPermissionStatus(campaign.status);
                          return (
                            <Badge variant={permission.color}>
                              {permission.label}
                            </Badge>
                          );
                        })()}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>권한 변경</DropdownMenuLabel>
                            {permissionChangeOptions
                              .filter((p) => p.value !== getCurrentPermission(campaign.status))
                              .map((permission) => (
                                <DropdownMenuItem
                                  key={permission.value}
                                  onClick={() =>
                                    handlePermissionChange(campaign, permission.value)
                                  }
                                >
                                  {permission.label}로 변경
                                </DropdownMenuItem>
                              ))}
                            <DropdownMenuSeparator />
                            <DropdownMenuLabel>상태 변경</DropdownMenuLabel>
                            {statusOptions
                              .filter((s) => s.value && s.value !== "all" && s.value !== campaign.status)
                              .map((status) => (
                                <DropdownMenuItem
                                  key={status.value}
                                  onClick={() =>
                                    handleStatusChange(campaign, status.value)
                                  }
                                >
                                  {status.label}로 변경
                                </DropdownMenuItem>
                              ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
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
            </>
          )}
        </CardContent>
      </Card>

      {/* Status Change Dialog */}
      <Dialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>상태 변경 확인</DialogTitle>
            <DialogDescription>
              {selectedCampaign && (
                <>
                  <strong>{selectedCampaign.name}</strong> 캠프의 상태를{" "}
                  <strong>{statusLabels[newStatus]}</strong>(으)로 변경하시겠습니까?
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setStatusDialogOpen(false)}
              disabled={updating}
            >
              취소
            </Button>
            <Button onClick={confirmStatusChange} loading={updating}>
              변경
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Permission Change Dialog */}
      <Dialog open={permissionDialogOpen} onOpenChange={setPermissionDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>권한 변경 확인</DialogTitle>
            <DialogDescription>
              {selectedCampaign && (
                <>
                  <strong>{selectedCampaign.name}</strong> 캠프의 권한을{" "}
                  <strong>{permissionOptions.find(p => p.value === newPermission)?.label}</strong>(으)로 변경하시겠습니까?
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setPermissionDialogOpen(false)}
              disabled={updating}
            >
              취소
            </Button>
            <Button onClick={confirmPermissionChange} loading={updating}>
              변경
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
