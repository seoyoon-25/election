"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  Building2,
  Users,
  Mail,
  LogOut,
  ArrowLeft,
  Shield,
  User,
} from "lucide-react";
import { getCurrentUser, isAuthenticated, logout } from "@/lib/auth";
import { User as UserType } from "@/types";
import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/admin", label: "대시보드", icon: LayoutDashboard, exact: true },
  { href: "/admin/campaigns", label: "캠프 관리", icon: Building2 },
  { href: "/admin/users", label: "사용자 관리", icon: Users },
  { href: "/admin/invitations", label: "초대 관리", icon: Mail },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserType | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const checkAuth = async () => {
      try {
        const userData = await getCurrentUser();
        if (!userData.is_superadmin) {
          router.push("/campaigns");
          return;
        }
        setUser(userData);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [router]);

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="px-4 md:px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/campaigns"
                className="flex items-center gap-2 text-gray-500 hover:text-gray-700"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline text-sm">캠프 목록</span>
              </Link>
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary-600" />
                <h1 className="text-lg font-semibold text-gray-900">
                  관리자
                </h1>
              </div>
            </div>
            <div className="flex items-center gap-2 md:gap-4">
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
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-57px)] hidden md:block">
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const isActive = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary-50 text-primary-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Mobile nav */}
        <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-10">
          <nav className="flex justify-around p-2">
            {navItems.map((item) => {
              const isActive = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex flex-col items-center gap-1 px-3 py-2 rounded-md text-xs font-medium transition-colors",
                    isActive
                      ? "text-primary-700"
                      : "text-gray-500 hover:text-gray-700"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Main content */}
        <main className="flex-1 p-4 md:p-6 pb-20 md:pb-6">{children}</main>
      </div>
    </div>
  );
}
