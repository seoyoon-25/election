"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, Clock, LogOut, RefreshCw } from "lucide-react";
import { Card, Button } from "@/components/ui";
import { api } from "@/lib/api";
import { logout } from "@/lib/auth";
import { APP_NAME } from "@/lib/constants";

export default function PendingApprovalPage() {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    // Try to get user info to show email
    const checkStatus = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          router.push("/login");
          return;
        }

        // Try to get user info via a special endpoint that doesn't require is_active
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          setUserEmail(data.email);

          // If user is now active, redirect to campaigns
          if (data.is_active) {
            router.push("/campaigns");
          }
        } else if (response.status === 403) {
          // User is inactive, which is expected
          // Try to get email from a different source or just show generic message
        } else {
          // Token invalid, redirect to login
          router.push("/login");
        }
      } catch {
        // Error checking status
      }
    };

    checkStatus();
  }, [router]);

  const handleCheckStatus = async () => {
    setChecking(true);
    try {
      const response = await api.get<{ is_active: boolean }>("/auth/me");
      if (response.is_active) {
        router.push("/campaigns");
      }
    } catch {
      // Still not approved or error
    } finally {
      setChecking(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <Card className="w-full max-w-md p-8 text-center">
        {/* 로고 */}
        <Link href="/" className="inline-flex items-center gap-2 mb-6">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-primary-foreground" />
          </div>
          <span className="text-2xl font-bold">{APP_NAME}</span>
        </Link>

        {/* 아이콘 */}
        <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Clock className="w-8 h-8 text-amber-600" />
        </div>

        {/* 메시지 */}
        <h1 className="text-xl font-bold text-slate-900 mb-2">
          승인 대기 중입니다
        </h1>
        <p className="text-slate-600 mb-6">
          회원가입이 완료되었습니다.
          <br />
          관리자의 승인 후 서비스를 이용하실 수 있습니다.
        </p>

        {userEmail && (
          <div className="bg-slate-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-slate-500">가입 이메일</p>
            <p className="font-medium text-slate-900">{userEmail}</p>
          </div>
        )}

        <div className="space-y-3">
          <Button
            variant="outline"
            className="w-full"
            onClick={handleCheckStatus}
            disabled={checking}
          >
            {checking ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            승인 상태 확인
          </Button>

          <Button
            variant="ghost"
            className="w-full text-slate-500"
            onClick={handleLogout}
          >
            <LogOut className="w-4 h-4 mr-2" />
            로그아웃
          </Button>
        </div>

        <p className="mt-6 text-sm text-slate-500">
          문의사항이 있으시면 관리자에게 연락하세요.
        </p>
      </Card>
    </div>
  );
}
