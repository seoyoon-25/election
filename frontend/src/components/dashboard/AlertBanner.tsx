"use client";

import Link from "next/link";
import { AlertTriangle, Calendar, CheckCircle, Clock, X } from "lucide-react";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface AlertItem {
  type: "urgent_approval" | "deadline" | "meeting" | "overdue";
  count: number;
  message: string;
  href: string;
}

interface AlertBannerProps {
  alerts: AlertItem[];
  className?: string;
}

const alertConfig = {
  urgent_approval: {
    icon: CheckCircle,
    color: "text-amber-600",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
  },
  deadline: {
    icon: Clock,
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
  },
  meeting: {
    icon: Calendar,
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
  },
  overdue: {
    icon: AlertTriangle,
    color: "text-red-600",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
  },
};

export function AlertBanner({ alerts, className }: AlertBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed || alerts.length === 0) {
    return null;
  }

  // 가장 긴급한 알림 타입 결정
  const priorityOrder: AlertItem["type"][] = [
    "overdue",
    "urgent_approval",
    "deadline",
    "meeting",
  ];
  const primaryAlert = alerts.sort(
    (a, b) => priorityOrder.indexOf(a.type) - priorityOrder.indexOf(b.type)
  )[0];

  const config = alertConfig[primaryAlert.type];
  const Icon = config.icon;

  return (
    <Alert
      className={cn(
        "relative",
        config.bgColor,
        config.borderColor,
        "border",
        className
      )}
    >
      <Icon className={cn("h-4 w-4", config.color)} />
      <AlertDescription className="flex items-center justify-between w-full">
        <div className="flex items-center gap-4 flex-wrap">
          {alerts.map((alert, index) => (
            <Link
              key={index}
              href={alert.href}
              className={cn(
                "flex items-center gap-1.5 text-sm font-medium hover:underline",
                alertConfig[alert.type].color
              )}
            >
              <span className="font-bold">{alert.count}건</span>
              <span>{alert.message}</span>
            </Link>
          ))}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 shrink-0"
          onClick={() => setDismissed(true)}
        >
          <X className="h-3 w-3" />
        </Button>
      </AlertDescription>
    </Alert>
  );
}
