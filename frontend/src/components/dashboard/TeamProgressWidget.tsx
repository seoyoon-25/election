"use client";

import { Users, AlertTriangle } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface TeamStat {
  teamName: string;
  total: number;
  completed: number;
  delayed: number;
}

interface TeamProgressWidgetProps {
  teamStats: TeamStat[];
  isLoading?: boolean;
  className?: string;
}

export function TeamProgressWidget({
  teamStats,
  isLoading,
  className,
}: TeamProgressWidgetProps) {
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Users className="h-4 w-4 text-primary" />
            팀별 진행 현황
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-4 w-20 bg-muted rounded" />
                <div className="h-2 w-full bg-muted rounded" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold flex items-center gap-2">
          <Users className="h-4 w-4 text-primary" />
          팀별 진행 현황
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {teamStats.map((team) => {
            const progressPercent =
              team.total > 0
                ? Math.round((team.completed / team.total) * 100)
                : 0;
            const hasDelayed = team.delayed > 0;

            return (
              <div key={team.teamName} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{team.teamName}</span>
                  <div className="flex items-center gap-2">
                    {hasDelayed && (
                      <span className="flex items-center gap-1 text-xs text-red-600">
                        <AlertTriangle className="h-3 w-3" />
                        지연 {team.delayed}건
                      </span>
                    )}
                    <span className="text-muted-foreground text-xs">
                      {team.completed}/{team.total}
                    </span>
                  </div>
                </div>
                <Progress
                  value={progressPercent}
                  className="h-2"
                  indicatorClassName={cn(
                    progressPercent >= 80
                      ? "bg-green-500"
                      : progressPercent >= 50
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  )}
                />
                <div className="flex justify-end">
                  <span className="text-[10px] text-muted-foreground">
                    {progressPercent}% 완료
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
