"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  Eye,
  Shield,
  CheckCircle,
  XCircle,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { AdminUser, AdminUserCampaign, PaginatedResponse } from "@/types";
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
  Avatar,
  AvatarImage,
  AvatarFallback,
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui";

interface AdminUserDetail extends AdminUser {
  campaigns: AdminUserCampaign[];
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchInput, setSearchInput] = useState("");

  // User detail sheet
  const [selectedUser, setSelectedUser] = useState<AdminUserDetail | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Approval confirmation dialog
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [userToApprove, setUserToApprove] = useState<AdminUser | null>(null);
  const [approvalAction, setApprovalAction] = useState<"approve" | "reject">("approve");
  const [updating, setUpdating] = useState(false);

  // Pending users count
  const [pendingCount, setPendingCount] = useState(0);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: "20",
      });
      if (search) params.append("search", search);
      if (activeFilter && activeFilter !== "all") params.append("is_active", activeFilter);

      const data = await api.get<PaginatedResponse<AdminUser>>(
        `/admin/users?${params.toString()}`
      );
      setUsers(data.items);
      setTotalPages(data.pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "사용자 목록을 불러올 수 없습니다");
    } finally {
      setLoading(false);
    }
  }, [page, search, activeFilter]);

  const fetchPendingCount = useCallback(async () => {
    try {
      const data = await api.get<PaginatedResponse<AdminUser>>(
        `/admin/users?is_active=false&page_size=1`
      );
      setPendingCount(data.total);
    } catch {
      // Ignore error for count
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    fetchPendingCount();
  }, [fetchPendingCount]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleViewUser = async (userId: number) => {
    setLoadingDetail(true);
    setDetailOpen(true);
    try {
      const data = await api.get<AdminUserDetail>(`/admin/users/${userId}`);
      setSelectedUser(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "사용자 정보를 불러올 수 없습니다");
      setDetailOpen(false);
    } finally {
      setLoadingDetail(false);
    }
  };

  const openApprovalDialog = (user: AdminUser, action: "approve" | "reject") => {
    setUserToApprove(user);
    setApprovalAction(action);
    setApprovalDialogOpen(true);
  };

  const confirmApproval = async () => {
    if (!userToApprove) return;

    const isActive = approvalAction === "approve";
    setUpdating(true);
    try {
      await api.patch(`/admin/users/${userToApprove.id}/activate?is_active=${isActive}`);
      // Refresh the users list
      fetchUsers();
      fetchPendingCount();
      // If viewing detail, refresh it too
      if (selectedUser && selectedUser.id === userToApprove.id) {
        setSelectedUser({ ...selectedUser, is_active: isActive });
      }
      setApprovalDialogOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "상태 변경에 실패했습니다");
    } finally {
      setUpdating(false);
    }
  };

  const handleToggleActive = async (userId: number, isActive: boolean) => {
    try {
      await api.patch(`/admin/users/${userId}/activate?is_active=${isActive}`);
      // Refresh the users list
      fetchUsers();
      fetchPendingCount();
      // If viewing detail, refresh it too
      if (selectedUser && selectedUser.id === userId) {
        setSelectedUser({ ...selectedUser, is_active: isActive });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "상태 변경에 실패했습니다");
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/users/export`,
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
      a.download = "users.csv";
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

  const formatDateTime = (dateString: string | undefined) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">사용자 관리</h1>
        <p className="text-gray-600 mt-1">모든 사용자를 관리합니다</p>
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
                  placeholder="이름, 이메일로 검색..."
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
              {pendingCount > 0 && (
                <Button
                  variant={activeFilter === "false" ? "default" : "outline"}
                  size="sm"
                  className="gap-2"
                  onClick={() => {
                    setActiveFilter(activeFilter === "false" ? "all" : "false");
                    setPage(1);
                  }}
                >
                  승인대기
                  <Badge variant="red" className="ml-1">{pendingCount}</Badge>
                </Button>
              )}

              <Select value={activeFilter} onValueChange={(value) => {
                setActiveFilter(value);
                setPage(1);
              }}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="전체 상태" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="true">승인됨</SelectItem>
                  <SelectItem value="false">승인대기</SelectItem>
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
          ) : users.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              사용자가 없습니다
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>사용자</TableHead>
                    <TableHead>상태</TableHead>
                    <TableHead>캠프</TableHead>
                    <TableHead>마지막 로그인</TableHead>
                    <TableHead>가입일</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-10 w-10">
                            {user.avatar_url ? (
                              <AvatarImage src={user.avatar_url} alt={user.full_name} />
                            ) : null}
                            <AvatarFallback>
                              {getInitials(user.full_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium flex items-center gap-2">
                              {user.full_name}
                              {user.is_superadmin && (
                                <Shield className="h-4 w-4 text-primary-600" />
                              )}
                            </div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          {user.is_active ? (
                            <Badge variant="green">활성</Badge>
                          ) : (
                            <Badge variant="yellow">승인 대기</Badge>
                          )}
                          {user.is_email_verified ? (
                            <span className="text-xs text-green-600 flex items-center gap-1">
                              <CheckCircle className="h-3 w-3" /> 이메일 인증됨
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400 flex items-center gap-1">
                              <XCircle className="h-3 w-3" /> 미인증
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="font-medium">{user.campaign_count}</span>
                        <span className="text-gray-500"> 개</span>
                      </TableCell>
                      <TableCell className="text-gray-500 text-sm">
                        {formatDateTime(user.last_login_at)}
                      </TableCell>
                      <TableCell className="text-gray-500 text-sm">
                        {formatDate(user.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {!user.is_active && !user.is_superadmin && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-green-600 hover:text-green-700 hover:bg-green-50"
                                onClick={() => openApprovalDialog(user, "approve")}
                              >
                                <CheckCircle className="h-4 w-4 mr-1" />
                                승인
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-gray-400 hover:text-red-600"
                                onClick={() => openApprovalDialog(user, "reject")}
                                title="거부"
                              >
                                <XCircle className="h-4 w-4" />
                              </Button>
                            </>
                          )}
                          {user.is_active && !user.is_superadmin && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-gray-500 hover:text-red-600"
                              onClick={() => openApprovalDialog(user, "reject")}
                              title="비활성화"
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewUser(user.id)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between px-6 py-4 border-t">
                <div className="text-sm text-gray-500">
                  총 {total.toLocaleString()}명 중 {(page - 1) * 20 + 1}-
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

      {/* User Detail Sheet */}
      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>사용자 상세</SheetTitle>
          </SheetHeader>
          {loadingDetail ? (
            <div className="space-y-4 mt-6">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          ) : selectedUser ? (
            <div className="mt-6 space-y-6">
              <div className="flex items-center gap-4">
                <Avatar className="h-16 w-16">
                  {selectedUser.avatar_url ? (
                    <AvatarImage
                      src={selectedUser.avatar_url}
                      alt={selectedUser.full_name}
                    />
                  ) : null}
                  <AvatarFallback className="text-lg">
                    {getInitials(selectedUser.full_name)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    {selectedUser.full_name}
                    {selectedUser.is_superadmin && (
                      <Badge variant="blue">슈퍼관리자</Badge>
                    )}
                  </h3>
                  <p className="text-gray-500">{selectedUser.email}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">상태</p>
                  <div className="flex items-center gap-2">
                    {selectedUser.is_active ? (
                      <Badge variant="green">활성</Badge>
                    ) : (
                      <Badge variant="yellow">승인 대기</Badge>
                    )}
                    {!selectedUser.is_superadmin && (
                      <Button
                        variant="outline"
                        size="sm"
                        className={selectedUser.is_active
                          ? "text-red-600 hover:text-red-700"
                          : "text-green-600 hover:text-green-700"}
                        onClick={() => handleToggleActive(selectedUser.id, !selectedUser.is_active)}
                      >
                        {selectedUser.is_active ? "비활성화" : "승인"}
                      </Button>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-500">이메일 인증</p>
                  <span
                    className={
                      selectedUser.is_email_verified
                        ? "text-green-600"
                        : "text-gray-400"
                    }
                  >
                    {selectedUser.is_email_verified ? "인증됨" : "미인증"}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">전화번호</p>
                  <p>{selectedUser.phone || "-"}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">가입일</p>
                  <p>{formatDate(selectedUser.created_at)}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-gray-500">마지막 로그인</p>
                  <p>{formatDateTime(selectedUser.last_login_at)}</p>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">
                  소속 캠프 ({selectedUser.campaigns.length})
                </h4>
                {selectedUser.campaigns.length === 0 ? (
                  <p className="text-gray-500 text-sm">소속된 캠프가 없습니다</p>
                ) : (
                  <div className="space-y-2">
                    {selectedUser.campaigns.map((c) => (
                      <div
                        key={c.campaign_id}
                        className="p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="font-medium">{c.campaign_name}</div>
                        <div className="text-sm text-gray-500 flex items-center gap-2 mt-1">
                          <Badge variant="blue">{c.role_name}</Badge>
                          {c.department_name && (
                            <span>{c.department_name}</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          가입일: {formatDate(c.joined_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>

      {/* Approval Confirmation Dialog */}
      <Dialog open={approvalDialogOpen} onOpenChange={setApprovalDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {approvalAction === "approve" ? "사용자 승인" : "사용자 비활성화"}
            </DialogTitle>
            <DialogDescription>
              {userToApprove && (
                <>
                  <strong>{userToApprove.full_name}</strong> ({userToApprove.email})
                  {approvalAction === "approve" ? (
                    <>님의 계정을 승인하시겠습니까? 승인 후 로그인이 가능합니다.</>
                  ) : (
                    <>님의 계정을 비활성화하시겠습니까? 비활성화 후 로그인이 차단됩니다.</>
                  )}
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setApprovalDialogOpen(false)}
              disabled={updating}
            >
              취소
            </Button>
            <Button
              variant={approvalAction === "approve" ? "default" : "destructive"}
              onClick={confirmApproval}
              loading={updating}
            >
              {approvalAction === "approve" ? (
                <>
                  <CheckCircle className="h-4 w-4 mr-1" />
                  승인
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-1" />
                  비활성화
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
