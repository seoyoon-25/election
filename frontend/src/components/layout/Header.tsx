"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams, usePathname } from "next/navigation";
import Link from "next/link";
import { LogOut, User, Menu, X, Home, LayoutDashboard, ClipboardList, Calendar, FileText, Users, Settings, Shield } from "lucide-react";
import { logout } from "@/lib/auth";
import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";

interface HeaderProps {
  user?: { full_name: string; email: string; is_superadmin?: boolean } | null;
}

export function Header({ user }: HeaderProps) {
  const router = useRouter();
  const params = useParams();
  const pathname = usePathname();
  const campaignId = params?.campaignId as string;
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      router.push("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const mobileNavItems = campaignId ? [
    { href: `/c/${campaignId}/dashboard`, label: "대시보드", icon: LayoutDashboard },
    { href: `/c/${campaignId}/tasks`, label: "태스크", icon: ClipboardList },
    { href: `/c/${campaignId}/calendar`, label: "캘린더", icon: Calendar },
    { href: `/c/${campaignId}/approvals`, label: "결재", icon: FileText },
    { href: `/c/${campaignId}/members`, label: "멤버", icon: Users },
    { href: "/campaigns", label: "캠페인 목록", icon: Home },
  ] : [];

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-4 md:px-6 py-3">
        <div className="flex items-center justify-between">
          {/* 모바일 메뉴 버튼 */}
          {campaignId && (
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label={mobileMenuOpen ? "메뉴 닫기" : "메뉴 열기"}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          )}

          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-primary-foreground" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900">캠프보드</h1>
          </Link>

          {mounted && user && (
            <div className="flex items-center gap-2 md:gap-4">
              {user.is_superadmin && (
                <Link href="/admin">
                  <Button variant="outline" size="sm">
                    <Shield className="h-4 w-4 sm:mr-1" />
                    <span className="hidden sm:inline">관리자</span>
                  </Button>
                </Link>
              )}
              <div className="hidden sm:flex items-center text-sm text-gray-600">
                <User className="h-4 w-4 mr-2" />
                {user.full_name}
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleLogout}
                loading={isLoggingOut}
              >
                <LogOut className="h-4 w-4 sm:mr-1" />
                <span className="hidden sm:inline">로그아웃</span>
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* 모바일 네비게이션 메뉴 */}
      {mounted && mobileMenuOpen && campaignId && (
        <nav className="md:hidden bg-white border-b shadow-sm" aria-label="모바일 메뉴">
          <div className="px-4 py-2 space-y-1">
            {mobileNavItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>
      )}
    </>
  );
}
