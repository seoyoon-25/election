"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn, getInitials } from "@/lib/utils";

interface UserAvatarProps {
  user: {
    id?: string;
    name: string;
    avatar_url?: string;
  };
  size?: "sm" | "md" | "lg";
  showTooltip?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: "h-6 w-6 text-xs",
  md: "h-8 w-8 text-sm",
  lg: "h-10 w-10 text-base",
};

export function UserAvatar({
  user,
  size = "md",
  showTooltip = true,
  className,
}: UserAvatarProps) {
  const avatar = (
    <Avatar className={cn(sizeClasses[size], className)}>
      {user.avatar_url && <AvatarImage src={user.avatar_url} alt={user.name} />}
      <AvatarFallback className="bg-primary/10 text-primary font-medium">
        {getInitials(user.name)}
      </AvatarFallback>
    </Avatar>
  );

  if (!showTooltip) {
    return avatar;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{avatar}</TooltipTrigger>
        <TooltipContent>
          <p>{user.name}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
