"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Bell,
  Calendar,
  CheckSquare,
  LogOut,
  Search,
  Settings,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { UserAvatar } from "@/components/common";
import { cn } from "@/lib/utils";

interface GlobalHeaderProps {
  user: {
    id: string;
    name: string;
    email: string;
    avatar_url?: string;
  };
  campaignId: string;
  campaignName: string;
  notificationCount?: number;
  onLogout: () => void;
}

export function GlobalHeader({
  user,
  campaignId,
  campaignName,
  notificationCount = 0,
  onLogout,
}: GlobalHeaderProps) {
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 gap-4">
        {/* 로고 & 캠페인 이름 */}
        <Link
          href={`/c/${campaignId}/dashboard`}
          className="flex items-center gap-2 font-semibold"
        >
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold">
            C
          </div>
          <span className="hidden md:inline-block truncate max-w-[200px]">
            {campaignName}
          </span>
        </Link>

        {/* 검색 바 */}
        <div className="flex-1 max-w-md hidden md:block">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="검색... (⌘K)"
              className="pl-8 bg-muted/50"
              onClick={() => setSearchOpen(true)}
            />
          </div>
        </div>

        {/* 우측 액션 버튼들 */}
        <div className="flex items-center gap-1 ml-auto">
          {/* 모바일 검색 버튼 */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setSearchOpen(true)}
          >
            <Search className="h-5 w-5" />
          </Button>

          {/* 알림 */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                {notificationCount > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-[10px]"
                  >
                    {notificationCount > 9 ? "9+" : notificationCount}
                  </Badge>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="end">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">알림</h4>
                <Button variant="ghost" size="sm" className="text-xs">
                  모두 읽음
                </Button>
              </div>
              <div className="space-y-2">
                <NotificationItem
                  title="결재 요청"
                  message="지출 결의서 #42가 승인 대기 중입니다"
                  time="5분 전"
                  unread
                />
                <NotificationItem
                  title="태스크 마감"
                  message="예산안 제출 마감이 오늘입니다"
                  time="1시간 전"
                  unread
                />
                <NotificationItem
                  title="일정 알림"
                  message="선대위 회의가 30분 후 시작됩니다"
                  time="2시간 전"
                />
              </div>
              <Button
                variant="link"
                size="sm"
                className="w-full mt-2 text-xs"
                asChild
              >
                <Link href={`/c/${campaignId}/notifications`}>
                  모든 알림 보기
                </Link>
              </Button>
            </PopoverContent>
          </Popover>

          {/* 내 태스크 */}
          <Button variant="ghost" size="icon" asChild>
            <Link href={`/c/${campaignId}/my-tasks`}>
              <CheckSquare className="h-5 w-5" />
            </Link>
          </Button>

          {/* 오늘 일정 */}
          <Button variant="ghost" size="icon" asChild>
            <Link href={`/c/${campaignId}/my-calendar`}>
              <Calendar className="h-5 w-5" />
            </Link>
          </Button>

          {/* 사용자 메뉴 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-9 w-9 rounded-full"
              >
                <UserAvatar user={{ name: user.name, avatar_url: user.avatar_url }} showTooltip={false} />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user.name}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href={`/c/${campaignId}/settings`}>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>설정</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/profile">
                  <User className="mr-2 h-4 w-4" />
                  <span>프로필</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onLogout} className="text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                <span>로그아웃</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}

function NotificationItem({
  title,
  message,
  time,
  unread,
}: {
  title: string;
  message: string;
  time: string;
  unread?: boolean;
}) {
  return (
    <div
      className={cn(
        "p-2 rounded-md text-sm cursor-pointer hover:bg-muted",
        unread && "bg-primary/5"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className={cn("font-medium truncate", unread && "text-primary")}>
            {title}
          </p>
          <p className="text-muted-foreground text-xs truncate">{message}</p>
        </div>
        <span className="text-[10px] text-muted-foreground whitespace-nowrap">
          {time}
        </span>
      </div>
    </div>
  );
}
