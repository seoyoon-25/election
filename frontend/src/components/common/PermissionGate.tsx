"use client";

import { ReactNode } from "react";
import { useOptionalPermission } from "@/contexts/PermissionContext";
import { Permission } from "@/lib/constants";

interface PermissionGateProps {
  children: ReactNode;
  permission?: Permission;
  permissions?: Permission[];
  requireAll?: boolean;
  fallback?: ReactNode;
}

export function PermissionGate({
  children,
  permission,
  permissions,
  requireAll = false,
  fallback = null,
}: PermissionGateProps) {
  const permissionContext = useOptionalPermission();

  // PermissionProvider 없으면 기본 숨김
  if (!permissionContext) {
    return <>{fallback}</>;
  }

  const { hasPermission, hasAnyPermission, hasAllPermissions } = permissionContext;

  // 단일 권한 체크
  if (permission) {
    if (!hasPermission(permission)) {
      return <>{fallback}</>;
    }
    return <>{children}</>;
  }

  // 복수 권한 체크
  if (permissions && permissions.length > 0) {
    const hasAccess = requireAll
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);

    if (!hasAccess) {
      return <>{fallback}</>;
    }
  }

  return <>{children}</>;
}

interface OwnerGateProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function OwnerGate({ children, fallback = null }: OwnerGateProps) {
  const permissionContext = useOptionalPermission();

  if (!permissionContext || !permissionContext.isOwner) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

interface AdminGateProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function AdminGate({ children, fallback = null }: AdminGateProps) {
  const permissionContext = useOptionalPermission();

  if (!permissionContext || (!permissionContext.isOwner && !permissionContext.isAdmin)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

interface DepartmentHeadGateProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export function DepartmentHeadGate({ children, fallback = null }: DepartmentHeadGateProps) {
  const permissionContext = useOptionalPermission();

  if (!permissionContext) {
    return <>{fallback}</>;
  }

  const { isOwner, isAdmin, isDepartmentHead } = permissionContext;

  if (!isOwner && !isAdmin && !isDepartmentHead) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
