import { HTMLAttributes } from "react";
import clsx from "clsx";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "gray" | "blue" | "green" | "yellow" | "red" | "purple";
}

export function Badge({ className, variant = "gray", children, ...props }: BadgeProps) {
  const variants = {
    gray: "bg-gray-100 text-gray-700",
    blue: "bg-blue-100 text-blue-700",
    green: "bg-green-100 text-green-700",
    yellow: "bg-yellow-100 text-yellow-700",
    red: "bg-red-100 text-red-700",
    purple: "bg-purple-100 text-purple-700",
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

// Helper for task status badges
export function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { variant: BadgeProps["variant"]; label: string }> = {
    backlog: { variant: "gray", label: "Backlog" },
    todo: { variant: "blue", label: "To Do" },
    in_progress: { variant: "yellow", label: "In Progress" },
    review: { variant: "purple", label: "Review" },
    done: { variant: "green", label: "Done" },
    pending: { variant: "yellow", label: "Pending" },
    approved: { variant: "green", label: "Approved" },
    rejected: { variant: "red", label: "Rejected" },
    cancelled: { variant: "gray", label: "Cancelled" },
    expired: { variant: "gray", label: "Expired" },
  };

  const { variant, label } = config[status] || { variant: "gray", label: status };

  return <Badge variant={variant}>{label}</Badge>;
}

// Helper for priority badges
export function PriorityBadge({ priority }: { priority: string }) {
  const config: Record<string, { variant: BadgeProps["variant"]; label: string }> = {
    low: { variant: "gray", label: "Low" },
    medium: { variant: "blue", label: "Medium" },
    high: { variant: "yellow", label: "High" },
    urgent: { variant: "red", label: "Urgent" },
  };

  const { variant, label } = config[priority] || { variant: "gray", label: priority };

  return <Badge variant={variant}>{label}</Badge>;
}
