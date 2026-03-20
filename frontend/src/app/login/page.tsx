"use client";

import { useState, FormEvent, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/auth";
import { api } from "@/lib/api";
import { Button, Input, Card } from "@/components/ui";
import { APP_NAME } from "@/lib/constants";
import { Shield, Mail, Lock, AlertCircle, Loader2 } from "lucide-react";

// Google 아이콘 컴포넌트
function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="currentColor"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="currentColor"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="currentColor"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="currentColor"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}

const ERROR_MESSAGES: Record<string, string> = {
  invalid_state: "인증 세션이 만료되었습니다. 다시 시도해주세요.",
  oauth_failed: "Google 인증에 실패했습니다. 다시 시도해주세요.",
  email_required: "이메일 정보를 가져올 수 없습니다.",
  account_disabled: "비활성화된 계정입니다. 관리자에게 문의하세요.",
  invitation_required: "초대받은 사용자만 가입할 수 있습니다.",
};

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  // Handle error from URL params (OAuth callback errors)
  useEffect(() => {
    const errorParam = searchParams.get("error");
    const emailParam = searchParams.get("email");

    if (errorParam) {
      let message = ERROR_MESSAGES[errorParam] || "로그인에 실패했습니다.";
      if (errorParam === "invitation_required" && emailParam) {
        message = `${emailParam} 계정은 초대가 필요합니다. 캠프 관리자에게 초대를 요청하세요.`;
      }
      setError(message);
    }
  }, [searchParams]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login({ email, password });
      router.push("/campaigns");
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인에 실패했습니다");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");
    setGoogleLoading(true);

    try {
      const response = await api.get<{ authorization_url: string }>(
        "/auth/google?redirect_uri=/login"
      );
      // Redirect to Google OAuth
      window.location.href = response.authorization_url;
    } catch (err) {
      if (err instanceof Error && err.message.includes("501")) {
        setError("Google 로그인이 설정되지 않았습니다.");
      } else {
        setError("Google 로그인을 시작할 수 없습니다.");
      }
      setGoogleLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md p-8">
      {/* 헤더 */}
      <div className="text-center mb-8">
        <Link href="/" className="inline-flex items-center gap-2 mb-4">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <Shield className="w-6 h-6 text-primary-foreground" />
          </div>
          <span className="text-2xl font-bold">{APP_NAME}</span>
        </Link>
        <p className="text-slate-600">계정에 로그인하세요</p>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Google 로그인 */}
      <Button
        type="button"
        variant="outline"
        className="w-full mb-6 h-11"
        onClick={handleGoogleLogin}
        disabled={googleLoading}
      >
        {googleLoading ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-slate-600" />
        ) : (
          <>
            <GoogleIcon className="w-5 h-5 mr-2" />
            Google로 계속하기
          </>
        )}
      </Button>

      {/* 구분선 */}
      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="bg-white px-4 text-slate-500">또는</span>
        </div>
      </div>

      {/* 이메일/비밀번호 폼 */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="이메일"
            required
            autoComplete="email"
            className="pl-10 h-11"
          />
        </div>

        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호"
            required
            autoComplete="current-password"
            className="pl-10 h-11"
          />
        </div>

        <Button type="submit" className="w-full h-11" disabled={loading}>
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
          ) : (
            "로그인"
          )}
        </Button>
      </form>

      {/* 푸터 */}
      <div className="mt-6 text-center">
        <p className="text-sm text-slate-500">
          계정이 없으신가요?{" "}
          <span className="text-slate-700">캠프 관리자에게 초대를 요청하세요</span>
        </p>
      </div>
    </Card>
  );
}

function LoginLoading() {
  return (
    <Card className="w-full max-w-md p-8">
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <Suspense fallback={<LoginLoading />}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
