"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn, getInitials } from "@/lib/utils";

interface User {
  id?: string;
  name: string;
  avatar_url?: string;
}

interface UserAvatarGroupProps {
  users: User[];
  max?: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "h-6 w-6 text-xs",
  md: "h-8 w-8 text-sm",
  lg: "h-10 w-10 text-base",
};

const overlapClasses = {
  sm: "-ml-2",
  md: "-ml-2.5",
  lg: "-ml-3",
};

export function UserAvatarGroup({
  users,
  max = 3,
  size = "md",
  className,
}: UserAvatarGroupProps) {
  const visibleUsers = users.slice(0, max);
  const remainingCount = users.length - max;

  return (
    <TooltipProvider>
      <div className={cn("flex items-center", className)}>
        {visibleUsers.map((user, index) => (
          <Tooltip key={user.id || index}>
            <TooltipTrigger asChild>
              <Avatar
                className={cn(
                  sizeClasses[size],
                  "border-2 border-background",
                  index > 0 && overlapClasses[size]
                )}
              >
                {user.avatar_url && (
                  <AvatarImage src={user.avatar_url} alt={user.name} />
                )}
                <AvatarFallback className="bg-primary/10 text-primary font-medium">
                  {getInitials(user.name)}
                </AvatarFallback>
              </Avatar>
            </TooltipTrigger>
            <TooltipContent>
              <p>{user.name}</p>
            </TooltipContent>
          </Tooltip>
        ))}
        {remainingCount > 0 && (
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={cn(
                  sizeClasses[size],
                  overlapClasses[size],
                  "flex items-center justify-center rounded-full border-2 border-background bg-muted text-muted-foreground font-medium cursor-default"
                )}
              >
                +{remainingCount}
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>
                {users
                  .slice(max)
                  .map((u) => u.name)
                  .join(", ")}
              </p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}
