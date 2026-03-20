"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Calendar,
  CheckSquare,
  ChevronDown,
  ClipboardList,
  FileText,
  FolderOpen,
  Home,
  LayoutDashboard,
  Megaphone,
  Settings,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface SidebarProps {
  campaignId: string;
  userRole?: string;
  pendingApprovals?: number;
}

export function Sidebar({
  campaignId,
  userRole = "member",
  pendingApprovals = 0,
}: SidebarProps) {
  const pathname = usePathname();
  const basePath = `/c/${campaignId}`;

  const isActive = (path: string) => pathname === path;

  const canManage = ["admin", "general_affairs"].includes(userRole);

  return (
    <aside className="hidden md:flex md:flex-col md:w-60 border-r bg-card">
      <div className="flex flex-col h-full py-4">
        {/* 대시보드 */}
        <div className="px-3 mb-2">
          <NavItem
            href={`${basePath}/dashboard`}
            icon={<LayoutDashboard className="h-4 w-4" />}
            label="대시보드"
            isActive={isActive(`${basePath}/dashboard`)}
          />
        </div>

        <Separator className="my-2" />

        {/* 내 업무 섹션 - 항상 펼침 */}
        <div className="px-3">
          <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            내 업무
          </h3>
          <nav className="space-y-1">
            <NavItem
              href={`${basePath}/my-tasks`}
              icon={<CheckSquare className="h-4 w-4" />}
              label="내 태스크"
              isActive={isActive(`${basePath}/my-tasks`)}
            />
            <NavItem
              href={`${basePath}/my-calendar`}
              icon={<Calendar className="h-4 w-4" />}
              label="내 일정"
              isActive={isActive(`${basePath}/my-calendar`)}
            />
            <NavItem
              href={`${basePath}/my-approvals`}
              icon={<ClipboardList className="h-4 w-4" />}
              label="내 결재함"
              isActive={isActive(`${basePath}/my-approvals`)}
              badge={pendingApprovals > 0 ? pendingApprovals : undefined}
            />
          </nav>
        </div>

        <Separator className="my-2" />

        {/* 팀 업무 섹션 */}
        <div className="px-3">
          <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            팀 업무
          </h3>
          <nav className="space-y-1">
            <NavItem
              href={`${basePath}/tasks`}
              icon={<ClipboardList className="h-4 w-4" />}
              label="태스크 보드"
              isActive={isActive(`${basePath}/tasks`)}
            />
            <NavItem
              href={`${basePath}/calendar`}
              icon={<Calendar className="h-4 w-4" />}
              label="팀 캘린더"
              isActive={isActive(`${basePath}/calendar`)}
            />
            <NavItem
              href={`${basePath}/approvals`}
              icon={<FileText className="h-4 w-4" />}
              label="결재 현황"
              isActive={isActive(`${basePath}/approvals`)}
            />
          </nav>
        </div>

        <Separator className="my-2" />

        {/* 자료실 섹션 - 접힘 가능 */}
        <div className="px-3">
          <Collapsible defaultOpen={false}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-between px-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider hover:bg-transparent"
              >
                자료실
                <ChevronDown className="h-3 w-3" />
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <nav className="space-y-1 mt-1">
                <NavItem
                  href={`${basePath}/files`}
                  icon={<FolderOpen className="h-4 w-4" />}
                  label="공유 파일"
                  isActive={isActive(`${basePath}/files`)}
                />
                <NavItem
                  href={`${basePath}/announcements`}
                  icon={<Megaphone className="h-4 w-4" />}
                  label="공지사항"
                  isActive={isActive(`${basePath}/announcements`)}
                />
              </nav>
            </CollapsibleContent>
          </Collapsible>
        </div>

        {/* 관리 섹션 - 관리자만 */}
        {canManage && (
          <>
            <Separator className="my-2" />
            <div className="px-3">
              <Collapsible defaultOpen={false}>
                <CollapsibleTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-between px-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider hover:bg-transparent"
                  >
                    관리
                    <ChevronDown className="h-3 w-3" />
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <nav className="space-y-1 mt-1">
                    <NavItem
                      href={`${basePath}/settings/members`}
                      icon={<Users className="h-4 w-4" />}
                      label="팀원 관리"
                      isActive={isActive(`${basePath}/settings/members`)}
                    />
                    <NavItem
                      href={`${basePath}/settings`}
                      icon={<Settings className="h-4 w-4" />}
                      label="캠페인 설정"
                      isActive={isActive(`${basePath}/settings`)}
                    />
                  </nav>
                </CollapsibleContent>
              </Collapsible>
            </div>
          </>
        )}

        {/* 하단 여백 */}
        <div className="flex-1" />

        {/* 캠페인 전환 링크 */}
        <div className="px-3 pt-2 border-t">
          <NavItem
            href="/campaigns"
            icon={<Home className="h-4 w-4" />}
            label="캠페인 목록"
            isActive={false}
          />
        </div>
      </div>
    </aside>
  );
}

interface NavItemProps {
  href: string;
  icon: React.ReactNode;
  label: string;
  isActive: boolean;
  badge?: number;
}

function NavItem({ href, icon, label, isActive, badge }: NavItemProps) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      )}
    >
      {icon}
      <span className="flex-1">{label}</span>
      {badge !== undefined && badge > 0 && (
        <Badge
          variant={isActive ? "secondary" : "destructive"}
          className="h-5 px-1.5 text-[10px]"
        >
          {badge > 99 ? "99+" : badge}
        </Badge>
      )}
    </Link>
  );
}
