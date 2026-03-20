import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type Priority = "low" | "medium" | "high" | "urgent";

interface PriorityBadgeProps {
  priority: Priority;
  size?: "sm" | "md";
  showIcon?: boolean;
  className?: string;
}

const priorityConfig: Record<
  Priority,
  { label: string; variant: Priority; icon: string }
> = {
  low: { label: "낮음", variant: "low", icon: "↓" },
  medium: { label: "보통", variant: "medium", icon: "→" },
  high: { label: "높음", variant: "high", icon: "↑" },
  urgent: { label: "긴급", variant: "urgent", icon: "⚡" },
};

export function PriorityBadge({
  priority,
  size = "md",
  showIcon = true,
  className,
}: PriorityBadgeProps) {
  const config = priorityConfig[priority];

  return (
    <Badge
      variant={config.variant}
      className={cn(
        size === "sm" && "px-1.5 py-0 text-[10px]",
        className
      )}
    >
      {showIcon && <span className="mr-0.5">{config.icon}</span>}
      {config.label}
    </Badge>
  );
}
