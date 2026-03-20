"use client";

import Link from "next/link";
import { ArrowRight, ClipboardList, Check, X } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState, CardSkeleton } from "@/components/common";
import { formatDateTime } from "@/lib/utils";

interface Approval {
  id: string;
  entity_type: string;
  entity_id: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  requested_by?: {
    name: string;
  };
}

interface PendingApprovalsWidgetProps {
  approvals: Approval[];
  isLoading?: boolean;
  error?: Error | null;
  campaignId: string;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}

const entityTypeLabels: Record<string, string> = {
  expense: "지출",
  document: "문서",
  schedule: "일정",
  task: "태스크",
};

export function PendingApprovalsWidget({
  approvals,
  isLoading,
  error,
  campaignId,
  onApprove,
  onReject,
}: PendingApprovalsWidgetProps) {
  const pendingApprovals = approvals.filter((a) => a.status === "pending");

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <ClipboardList className="h-4 w-4 text-primary" />
          결재 대기
          {pendingApprovals.length > 0 && (
            <Badge variant="destructive" className="h-5 px-1.5 text-[10px]">
              {pendingApprovals.length}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <CardSkeleton key={i} className="h-16" />
            ))}
          </div>
        )}

        {error && (
          <ErrorState
            message="결재 목록을 불러오지 못했습니다"
            onRetry={() => window.location.reload()}
          />
        )}

        {!isLoading && !error && pendingApprovals.length === 0 && (
          <EmptyState
            title="대기 중인 결재가 없습니다"
            icon={<ClipboardList className="h-8 w-8 text-muted-foreground" />}
          />
        )}

        {!isLoading && !error && pendingApprovals.length > 0 && (
          <>
            <div className="space-y-2 flex-1">
              {pendingApprovals.slice(0, 4).map((approval) => (
                <ApprovalItem
                  key={approval.id}
                  approval={approval}
                  onApprove={() => onApprove?.(approval.id)}
                  onReject={() => onReject?.(approval.id)}
                />
              ))}
            </div>
            <div className="pt-3 mt-auto border-t">
              <Link
                href={`/c/${campaignId}/my-approvals`}
                className="flex items-center justify-center text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                전체보기
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function ApprovalItem({
  approval,
  onApprove,
  onReject,
}: {
  approval: Approval;
  onApprove?: () => void;
  onReject?: () => void;
}) {
  const typeLabel = entityTypeLabels[approval.entity_type] || approval.entity_type;

  return (
    <div className="p-3 rounded-md border bg-card">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm">
            {typeLabel} #{approval.entity_id.slice(-4)}
          </p>
          <p className="text-xs text-muted-foreground">
            {approval.requested_by?.name || "알 수 없음"} · {formatDateTime(approval.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-1">
          {onApprove && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-green-600 hover:text-green-700 hover:bg-green-50"
              onClick={onApprove}
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
          {onReject && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-red-600 hover:text-red-700 hover:bg-red-50"
              onClick={onReject}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
