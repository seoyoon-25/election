import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 날짜를 상대적인 텍스트로 변환
 * 예: "오늘", "내일", "3일 후", "3일 전"
 */
export function formatRelativeDate(date: Date | string): string {
  const targetDate = new Date(date);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  targetDate.setHours(0, 0, 0, 0);

  const diffTime = targetDate.getTime() - today.getTime();
  const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "오늘";
  if (diffDays === 1) return "내일";
  if (diffDays === -1) return "어제";
  if (diffDays > 0 && diffDays <= 7) return `${diffDays}일 후`;
  if (diffDays < 0 && diffDays >= -7) return `${Math.abs(diffDays)}일 전`;

  return targetDate.toLocaleDateString("ko-KR", {
    month: "short",
    day: "numeric",
  });
}

/**
 * 마감일까지 남은 시간의 긴급도 판단
 */
export function getDueStatus(
  dueDate: Date | string | undefined
): "overdue" | "today" | "tomorrow" | "soon" | "normal" | null {
  if (!dueDate) return null;

  const target = new Date(dueDate);
  const now = new Date();
  target.setHours(23, 59, 59, 999);

  const diffMs = target.getTime() - now.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);

  if (diffMs < 0) return "overdue";
  if (diffHours <= 24) return "today";
  if (diffHours <= 48) return "tomorrow";
  if (diffHours <= 72) return "soon";
  return "normal";
}

/**
 * 사용자 이름에서 이니셜 추출
 */
export function getInitials(name: string): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].charAt(0).toUpperCase();
  }
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

/**
 * 시간 포맷팅 (HH:mm)
 */
export function formatTime(date: Date | string): string {
  return new Date(date).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/**
 * 날짜 + 시간 포맷팅
 */
export function formatDateTime(date: Date | string): string {
  return new Date(date).toLocaleString("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
