import { Calendar, AlertTriangle, Clock } from "lucide-react";
import { cn, formatRelativeDate, getDueStatus } from "@/lib/utils";

interface DueDateDisplayProps {
  dueDate: string | Date | undefined;
  showIcon?: boolean;
  showTime?: boolean;
  className?: string;
}

export function DueDateDisplay({
  dueDate,
  showIcon = true,
  showTime = false,
  className,
}: DueDateDisplayProps) {
  if (!dueDate) return null;

  const status = getDueStatus(dueDate);
  const date = new Date(dueDate);
  const relativeText = formatRelativeDate(date);

  const timeText = showTime
    ? date.toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      })
    : "";

  const statusStyles = {
    overdue: "text-red-600 bg-red-50",
    today: "text-amber-600 bg-amber-50",
    tomorrow: "text-yellow-600 bg-yellow-50",
    soon: "text-blue-600 bg-blue-50",
    normal: "text-muted-foreground",
  };

  const Icon = status === "overdue" ? AlertTriangle : status === "today" ? Clock : Calendar;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-xs",
        status && statusStyles[status],
        status && status !== "normal" && "px-1.5 py-0.5 rounded",
        className
      )}
    >
      {showIcon && <Icon className="h-3 w-3" />}
      <span>
        {relativeText}
        {showTime && timeText && ` ${timeText}`}
      </span>
      {status === "overdue" && (
        <span className="font-medium ml-0.5">지연</span>
      )}
    </span>
  );
}
