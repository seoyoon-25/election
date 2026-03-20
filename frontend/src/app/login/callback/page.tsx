"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");

    if (accessToken && refreshToken) {
      // Store tokens
      api.setToken(accessToken);
      api.setRefreshToken(refreshToken);

      // Redirect to campaigns
      router.replace("/campaigns");
    } else {
      // No tokens - redirect to login with error
      router.replace("/login?error=oauth_failed");
    }
  }, [router, searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4" />
        <p className="text-slate-600">로그인 처리 중...</p>
      </div>
    </div>
  );
}
