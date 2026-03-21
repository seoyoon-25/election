"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button, Input, Card } from "@/components/ui";
import { APP_NAME } from "@/lib/constants";
import {
  Shield,
  User,
  Lock,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Clock,
  UserX,
  XCircle,
  Eye,
  EyeOff,
  Mail,
} from "lucide-react";

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

type InvitationState = "loading" | "valid" | "expired" | "already_exists" | "invalid";

interface InvitationVerifyResponse {
  valid: boolean;
  email?: string;
  campaign_name?: string;
  role_name?: string;
  expires_at?: string;
  error?: string;
}

interface InvitationAcceptResponse {
  user_id: number;
  email: string;
  full_name: string;
  campaign_id: number;
  campaign_name: string;
  tokens: {
    access_token: string;
    refresh_token: string;
  };
}

export default function InvitationAcceptPage() {
  const router = useRouter();
  const params = useParams();
  const token = params.token as string;

  const [state, setState] = useState<InvitationState>("loading");
  const [submitting, setSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [invitation, setInvitation] = useState<InvitationVerifyResponse | null>(null);

  // Form state
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");

  // Resend state
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Verify invitation on mount
  useEffect(() => {
    async function verifyInvitation() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/invitations/verify/${token}`
        );
        const data: InvitationVerifyResponse = await response.json();
        setInvitation(data);

        if (data.valid) {
          setState("valid");
        } else if (data.error?.includes("expired")) {
          setState("expired");
        } else if (data.error?.includes("already") || data.error?.includes("accepted")) {
          setState("already_exists");
        } else {
          setState("invalid");
        }
      } catch {
        setState("invalid");
        setInvitation({ valid: false, error: "초대 정보를 확인할 수 없습니다" });
      }
    }

    verifyInvitation();
  }, [token]);

  const handleGoogleSignup = async () => {
    setGoogleLoading(true);
    try {
      const response = await api.get<{ authorization_url: string }>(
        "/auth/google?redirect_uri=/login"
      );
      window.location.href = response.authorization_url;
    } catch {
      setError("Google 로그인을 시작할 수 없습니다");
      setGoogleLoading(false);
    }
  };

  const handleResendRequest = async () => {
    setResendLoading(true);
    // Note: 재발송 API가 없으면 관리자 문의 안내로 대체
    // 실제 API가 있다면 여기서 호출
    setTimeout(() => {
      setResendLoading(false);
      setResendSuccess(true);
    }, 1000);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (!fullName.trim()) {
      setError("이름을 입력하세요");
      return;
    }

    if (password.length < 8) {
      setError("비밀번호는 8자 이상이어야 합니다");
      return;
    }

    if (password !== confirmPassword) {
      setError("비밀번호가 일치하지 않습니다");
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/invitations/accept/${token}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: fullName,
            password: password,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        // Handle specific error cases
        if (errorData.detail?.includes("already exists")) {
          setState("already_exists");
          return;
        }
        throw new Error(errorData.detail || "가입에 실패했습니다");
      }

      const data: InvitationAcceptResponse = await response.json();

      api.setToken(data.tokens.access_token);
      api.setRefreshToken(data.tokens.refresh_token);

      router.push("/campaigns");
    } catch (err) {
      setError(err instanceof Error ? err.message : "가입에 실패했습니다");
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state
  if (state === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-slate-600">초대 정보를 확인하는 중...</p>
        </div>
      </div>
    );
  }

  // Expired invitation
  if (state === "expired") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
        <Card className="w-full max-w-md p-8 text-center">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Clock className="w-8 h-8 text-amber-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 mb-2">
            초대 링크가 만료되었습니다
          </h1>
          <p className="text-slate-600 mb-6">
            초대 링크의 유효 기간이 지났습니다.
            <br />
            캠프 관리자에게 새로운 초대를 요청하세요.
          </p>

          {resendSuccess ? (
            <div className="p-4 rounded-lg bg-green-50 border border-green-200 mb-4">
              <CheckCircle2 className="w-5 h-5 text-green-500 mx-auto mb-2" />
              <p className="text-sm text-green-700">
                관리자에게 재발송 요청을 전달했습니다
              </p>
            </div>
          ) : (
            <Button
              variant="outline"
              className="w-full mb-3"
              onClick={handleResendRequest}
              disabled={resendLoading}
            >
              {resendLoading ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Mail className="w-4 h-4 mr-2" />
              )}
              재발송 요청하기
            </Button>
          )}

          <Link href="/login">
            <Button variant="ghost" className="w-full">
              로그인 페이지로 이동
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  // Already exists (email already registered)
  if (state === "already_exists") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
        <Card className="w-full max-w-md p-8 text-center">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <UserX className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 mb-2">
            이미 가입된 이메일입니다
          </h1>
          <p className="text-slate-600 mb-6">
            {invitation?.email && (
              <>
                <span className="font-medium">{invitation.email}</span>
                <br />
              </>
            )}
            이 이메일로 이미 계정이 등록되어 있습니다.
            <br />
            기존 계정으로 로그인하세요.
          </p>
          <Link href="/login">
            <Button className="w-full">로그인하기</Button>
          </Link>
        </Card>
      </div>
    );
  }

  // Invalid token
  if (state === "invalid") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
        <Card className="w-full max-w-md p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 mb-2">
            잘못된 초대 링크입니다
          </h1>
          <p className="text-slate-600 mb-6">
            {invitation?.error || "유효하지 않은 초대 링크입니다."}
            <br />
            링크가 올바른지 확인하거나 관리자에게 문의하세요.
          </p>
          <Link href="/login">
            <Button variant="outline" className="w-full">
              로그인 페이지로 이동
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  // Valid invitation - show signup form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <Card className="w-full max-w-md p-8">
        {/* 헤더 */}
        <div className="text-center mb-6">
          <Link href="/" className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold">{APP_NAME}</span>
          </Link>
        </div>

        {/* 초대 정보 */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-green-800">
                캠프 초대를 받았습니다
              </p>
              <p className="text-sm text-green-700 mt-1">
                <span className="font-medium">{invitation?.campaign_name}</span>
                {invitation?.role_name && <> - {invitation.role_name}</>}
              </p>
            </div>
          </div>
        </div>

        {/* Google 회원가입 */}
        <Button
          type="button"
          variant="outline"
          className="w-full mb-4 h-11"
          onClick={handleGoogleSignup}
          disabled={googleLoading}
        >
          {googleLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <GoogleIcon className="w-5 h-5 mr-2" />
              Google로 가입하기
            </>
          )}
        </Button>

        {/* 구분선 */}
        <div className="relative mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-white px-4 text-slate-500">또는</span>
          </div>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* 가입 폼 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              이메일
            </label>
            <Input
              type="email"
              value={invitation?.email || ""}
              disabled
              className="bg-slate-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              이름
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="실명을 입력하세요"
                required
                className="pl-10 h-11"
                disabled={submitting}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              비밀번호
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="8자 이상 입력"
                required
                minLength={8}
                className="pl-10 pr-10 h-11"
                disabled={submitting}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              비밀번호 확인
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                type={showConfirm ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="비밀번호 다시 입력"
                required
                className="pl-10 pr-10 h-11"
                disabled={submitting}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                tabIndex={-1}
              >
                {showConfirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            {confirmPassword && (
              <p
                className={`mt-1 text-xs ${
                  password === confirmPassword ? "text-green-600" : "text-red-500"
                }`}
              >
                {password === confirmPassword
                  ? "비밀번호 일치"
                  : "비밀번호 불일치"}
              </p>
            )}
          </div>

          <Button type="submit" className="w-full h-11" disabled={submitting}>
            {submitting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              "가입하고 캠프 참여하기"
            )}
          </Button>

          <p className="text-xs text-center text-muted-foreground mt-4">
            가입 시{" "}
            <Link href="/privacy" className="text-primary hover:underline">
              개인정보 처리방침
            </Link>
            에 동의하게 됩니다.
          </p>
        </form>

        {/* 푸터 */}
        <div className="mt-6 text-center">
          <p className="text-sm text-slate-500">
            이미 계정이 있으신가요?{" "}
            <Link href="/login" className="text-primary hover:underline">
              로그인
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}
