"use client";

import { ReactNode, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useOptionalPermission } from "@/contexts/PermissionContext";
import { Permission } from "@/lib/constants";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RequirePermissionProps {
  children: ReactNode;
  permission?: Permission;
  permissions?: Permission[];
  requireAll?: boolean;
  redirectTo?: string;
  showAccessDenied?: boolean;
}

export function RequirePermission({
  children,
  permission,
  permissions,
  requireAll = false,
  redirectTo,
  showAccessDenied = true,
}: RequirePermissionProps) {
  const router = useRouter();
  const params = useParams();
  const campaignId = params.campaignId as string;
  const permissionContext = useOptionalPermission();

  const hasAccess = (() => {
    if (!permissionContext) return false;

    const { hasPermission, hasAnyPermission, hasAllPermissions } = permissionContext;

    if (permission) {
      return hasPermission(permission);
    }

    if (permissions && permissions.length > 0) {
      return requireAll
        ? hasAllPermissions(permissions)
        : hasAnyPermission(permissions);
    }

    return true;
  })();

  useEffect(() => {
    if (!hasAccess && redirectTo) {
      router.push(redirectTo);
    }
  }, [hasAccess, redirectTo, router]);

  if (!hasAccess) {
    if (redirectTo) {
      return (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
        </div>
      );
    }

    if (showAccessDenied) {
      return <AccessDenied campaignId={campaignId} />;
    }

    return null;
  }

  return <>{children}</>;
}

interface AccessDeniedProps {
  campaignId?: string;
}

function AccessDenied({ campaignId }: AccessDeniedProps) {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
      <div className="rounded-full bg-destructive/10 p-4 mb-4">
        <AlertTriangle className="h-8 w-8 text-destructive" />
      </div>
      <h2 className="text-xl font-semibold mb-2">접근 권한이 없습니다</h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        이 페이지를 볼 수 있는 권한이 없습니다.
        필요한 경우 캠페인 관리자에게 문의하세요.
      </p>
      <div className="flex gap-3">
        <Button variant="outline" onClick={() => router.back()}>
          이전 페이지
        </Button>
        {campaignId && (
          <Button onClick={() => router.push(`/c/${campaignId}/dashboard`)}>
            대시보드로 이동
          </Button>
        )}
      </div>
    </div>
  );
}

export function RequireAdmin({ children }: { children: ReactNode }) {
  const permissionContext = useOptionalPermission();
  const router = useRouter();
  const params = useParams();
  const campaignId = params.campaignId as string;

  const hasAccess = permissionContext?.isOwner || permissionContext?.isAdmin;

  if (!hasAccess) {
    return <AccessDenied campaignId={campaignId} />;
  }

  return <>{children}</>;
}

export function RequireOwner({ children }: { children: ReactNode }) {
  const permissionContext = useOptionalPermission();
  const params = useParams();
  const campaignId = params.campaignId as string;

  if (!permissionContext?.isOwner) {
    return <AccessDenied campaignId={campaignId} />;
  }

  return <>{children}</>;
}
