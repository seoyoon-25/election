// User & Auth Types
export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  avatar_url?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

// Campaign Types
export interface Campaign {
  id: number;
  name: string;
  slug: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CampaignMembership {
  id: number;
  campaign_id: number;
  user_id: number;
  role_id: number;
  campaign: Campaign;
  role: Role;
}

export interface Role {
  id: number;
  name: string;
  permissions: string[];
}

// Task Types
export type TaskStatus = "backlog" | "todo" | "in_progress" | "review" | "done";
export type TaskPriority = "low" | "medium" | "high" | "urgent";

export interface Task {
  id: number;
  campaign_id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id?: number;
  assignee?: User;
  due_date?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee_id?: number;
  due_date?: string;
}

// Calendar Types
export type EventType = "meeting" | "campaign" | "deadline" | "briefing" | "other";

export interface CalendarEvent {
  id: string | number;
  campaign_id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  location?: string;
  type?: EventType;
  is_all_day: boolean;
  attendees?: { id: number; full_name?: string; email?: string; avatar_url?: string }[];
  created_at: string;
}

// Approval Types
export type ApprovalStatus = "pending" | "approved" | "rejected" | "cancelled" | "expired";

export interface ApprovalWorkflow {
  id: number;
  campaign_id: number;
  name: string;
  description?: string;
  entity_type: string;
  is_active: boolean;
}

export interface ApprovalRequest {
  id: number;
  workflow_id: number;
  campaign_id: number;
  entity_type: string;
  entity_id: number;
  status: ApprovalStatus;
  requested_by_id: number;
  requested_by?: { id: number; full_name?: string; email?: string };
  created_at: string;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
}
