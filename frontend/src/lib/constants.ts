/**
 * 캠프보드 상수 정의
 * 프론트엔드 가드 및 UI에서 재사용
 */

// 앱 정보
export const APP_NAME = "캠프보드";
export const APP_DESCRIPTION = "선거캠프 실무를 한곳에서 관리하는 업무 공간";
export const APP_TAGLINE = "선거캠프 업무 관리의 새로운 기준";

// 역할 정의
export const ROLES = {
  ADMIN: "admin",
  GENERAL_AFFAIRS: "general-affairs",
  POLICY: "policy",
  COMMUNICATIONS: "communications",
  STAFF: "staff",
} as const;

export type RoleSlug = (typeof ROLES)[keyof typeof ROLES];

export const ROLE_LABELS: Record<RoleSlug, string> = {
  [ROLES.ADMIN]: "관리자",
  [ROLES.GENERAL_AFFAIRS]: "총무",
  [ROLES.POLICY]: "정책",
  [ROLES.COMMUNICATIONS]: "홍보",
  [ROLES.STAFF]: "스태프",
};

export const ROLE_DESCRIPTIONS: Record<RoleSlug, string> = {
  [ROLES.ADMIN]: "캠프 전체 관리 권한",
  [ROLES.GENERAL_AFFAIRS]: "행정/운영 담당",
  [ROLES.POLICY]: "정책 기획 담당",
  [ROLES.COMMUNICATIONS]: "미디어/SNS 담당",
  [ROLES.STAFF]: "일반 참여자",
};

// 권한 정의
export const PERMISSIONS = {
  // 멤버 관리
  MEMBERS_READ: "members:read",
  MEMBERS_INVITE: "members:invite",
  MEMBERS_UPDATE: "members:update",
  MEMBERS_REMOVE: "members:remove",
  // 태스크
  TASKS_READ: "tasks:read",
  TASKS_CREATE: "tasks:create",
  TASKS_UPDATE: "tasks:update",
  TASKS_DELETE: "tasks:delete",
  TASKS_ASSIGN: "tasks:assign",
  // 승인
  APPROVALS_READ: "approvals:read",
  APPROVALS_CREATE: "approvals:create",
  APPROVALS_APPROVE: "approvals:approve",
  // 일정
  CALENDAR_READ: "calendar:read",
  CALENDAR_CREATE: "calendar:create",
  CALENDAR_UPDATE: "calendar:update",
  // 설정
  SETTINGS_READ: "settings:read",
  SETTINGS_UPDATE: "settings:update",
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

// 역할별 기본 권한
export const ROLE_PERMISSIONS: Record<RoleSlug, Permission[]> = {
  [ROLES.ADMIN]: Object.values(PERMISSIONS),
  [ROLES.GENERAL_AFFAIRS]: [
    PERMISSIONS.MEMBERS_READ,
    PERMISSIONS.MEMBERS_INVITE,
    PERMISSIONS.MEMBERS_UPDATE,
    PERMISSIONS.TASKS_READ,
    PERMISSIONS.TASKS_CREATE,
    PERMISSIONS.TASKS_UPDATE,
    PERMISSIONS.TASKS_ASSIGN,
    PERMISSIONS.APPROVALS_READ,
    PERMISSIONS.APPROVALS_CREATE,
    PERMISSIONS.APPROVALS_APPROVE,
    PERMISSIONS.CALENDAR_READ,
    PERMISSIONS.CALENDAR_CREATE,
    PERMISSIONS.CALENDAR_UPDATE,
    PERMISSIONS.SETTINGS_READ,
  ],
  [ROLES.POLICY]: [
    PERMISSIONS.MEMBERS_READ,
    PERMISSIONS.TASKS_READ,
    PERMISSIONS.TASKS_CREATE,
    PERMISSIONS.TASKS_UPDATE,
    PERMISSIONS.APPROVALS_READ,
    PERMISSIONS.APPROVALS_CREATE,
    PERMISSIONS.CALENDAR_READ,
  ],
  [ROLES.COMMUNICATIONS]: [
    PERMISSIONS.MEMBERS_READ,
    PERMISSIONS.TASKS_READ,
    PERMISSIONS.TASKS_CREATE,
    PERMISSIONS.TASKS_UPDATE,
    PERMISSIONS.CALENDAR_READ,
    PERMISSIONS.CALENDAR_CREATE,
    PERMISSIONS.CALENDAR_UPDATE,
  ],
  [ROLES.STAFF]: [
    PERMISSIONS.MEMBERS_READ,
    PERMISSIONS.TASKS_READ,
    PERMISSIONS.TASKS_CREATE,
    PERMISSIONS.APPROVALS_READ,
    PERMISSIONS.CALENDAR_READ,
  ],
};

// 권한 체크 유틸
export function hasPermission(
  userPermissions: string[],
  requiredPermission: Permission
): boolean {
  return userPermissions.includes(requiredPermission);
}

export function hasAnyPermission(
  userPermissions: string[],
  requiredPermissions: Permission[]
): boolean {
  return requiredPermissions.some((p) => userPermissions.includes(p));
}

export function hasAllPermissions(
  userPermissions: string[],
  requiredPermissions: Permission[]
): boolean {
  return requiredPermissions.every((p) => userPermissions.includes(p));
}
