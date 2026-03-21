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

// 권한 정의 (백엔드 Permission enum과 동기화)
export const PERMISSIONS = {
  // Campaign management
  CAMPAIGN_VIEW: "campaign:view",
  CAMPAIGN_EDIT: "campaign:edit",
  CAMPAIGN_MANAGE_MEMBERS: "campaign:manage_members",
  CAMPAIGN_MANAGE_ROLES: "campaign:manage_roles",
  CAMPAIGN_DELETE: "campaign:delete",

  // Department management
  DEPARTMENT_VIEW: "department:view",
  DEPARTMENT_CREATE: "department:create",
  DEPARTMENT_EDIT: "department:edit",
  DEPARTMENT_DELETE: "department:delete",

  // Task management
  TASK_VIEW_ALL: "task:view_all",
  TASK_VIEW_DEPARTMENT: "task:view_department",
  TASK_CREATE: "task:create",
  TASK_EDIT_OWN: "task:edit_own",
  TASK_EDIT_ALL: "task:edit_all",
  TASK_DELETE: "task:delete",
  TASK_ASSIGN: "task:assign",

  // Board management
  BOARD_CREATE: "board:create",
  BOARD_EDIT: "board:edit",
  BOARD_DELETE: "board:delete",

  // Approval workflow
  APPROVAL_REQUEST: "approval:request",
  APPROVAL_DECIDE: "approval:decide",
  APPROVAL_MANAGE_WORKFLOWS: "approval:manage_workflows",

  // Calendar/Events
  EVENT_VIEW: "event:view",
  EVENT_CREATE: "event:create",
  EVENT_EDIT_OWN: "event:edit_own",
  EVENT_EDIT_ALL: "event:edit_all",
  EVENT_DELETE: "event:delete",

  // Files/Attachments
  FILE_UPLOAD: "file:upload",
  FILE_DELETE_OWN: "file:delete_own",
  FILE_DELETE_ALL: "file:delete_all",

  // Notifications/Webhooks
  WEBHOOK_MANAGE: "webhook:manage",

  // Audit
  AUDIT_VIEW: "audit:view",
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

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
