"use client";

import {
  createContext,
  useContext,
  ReactNode,
  useMemo,
} from "react";
import { Permission, PERMISSIONS } from "@/lib/constants";

interface PermissionContextValue {
  permissions: string[];
  roleName: string;
  roleSlug: string;
  isOwner: boolean;
  isAdmin: boolean;
  isDepartmentHead: boolean;
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  canManageMembers: boolean;
  canManageSettings: boolean;
}

const PermissionContext = createContext<PermissionContextValue | null>(null);

interface PermissionProviderProps {
  children: ReactNode;
  permissions: string[];
  roleName: string;
  roleSlug: string;
  isOwner: boolean;
  isAdmin: boolean;
  isDepartmentHead: boolean;
}

export function PermissionProvider({
  children,
  permissions,
  roleName,
  roleSlug,
  isOwner,
  isAdmin,
  isDepartmentHead,
}: PermissionProviderProps) {
  const value = useMemo<PermissionContextValue>(() => {
    const hasPermission = (permission: Permission): boolean => {
      return permissions.includes(permission);
    };

    const hasAnyPermission = (perms: Permission[]): boolean => {
      return perms.some((p) => permissions.includes(p));
    };

    const hasAllPermissions = (perms: Permission[]): boolean => {
      return perms.every((p) => permissions.includes(p));
    };

    return {
      permissions,
      roleName,
      roleSlug,
      isOwner,
      isAdmin,
      isDepartmentHead,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      canManageMembers: hasPermission(PERMISSIONS.CAMPAIGN_MANAGE_MEMBERS),
      canManageSettings: hasPermission(PERMISSIONS.CAMPAIGN_EDIT),
    };
  }, [permissions, roleName, roleSlug, isOwner, isAdmin, isDepartmentHead]);

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
}

export function usePermission(): PermissionContextValue {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error("usePermission must be used within a PermissionProvider");
  }
  return context;
}

export function useOptionalPermission(): PermissionContextValue | null {
  return useContext(PermissionContext);
}

export { PERMISSIONS };
