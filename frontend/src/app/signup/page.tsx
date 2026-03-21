"use client";

import { useState, FormEvent, Suspense } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button, Input, Card } from "@/components/ui";
import { APP_NAME } from "@/lib/constants";
import { Shield, Mail, Lock, User, Phone, AlertCircle, Loader2, CheckCircle } from "lucide-react";

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

function SignupForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // 비밀번호 확인
    if (password !== confirmPassword) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }

    // 비밀번호 길이 확인
    if (password.length < 8) {
      setError("비밀번호는 최소 8자 이상이어야 합니다.");
      return;
    }

    setLoading(true);

    try {
      await api.post("/auth/register", {
        email,
        full_name: fullName,
        password,
        phone: phone || undefined,
      });

      setSuccess(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "회원가입에 실패했습니다";
      if (errorMessage.includes("409") || errorMessage.toLowerCase().includes("already")) {
        setError("이미 등록된 이메일입니다.");
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setError("");
    setGoogleLoading(true);

    try {
      const response = await api.get<{ authorization_url: string }>(
        "/auth/google?redirect_uri=/login"
      );
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

  if (success) {
    return (
      <Card className="w-full max-w-md p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2">회원가입 완료</h2>
          <p className="text-slate-600 mb-6">
            계정이 생성되었습니다.<br />
            관리자 승인 후 로그인할 수 있습니다.
          </p>
          <Link href="/login">
            <Button className="w-full">로그인 페이지로 이동</Button>
          </Link>
        </div>
      </Card>
    );
  }

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
        <p className="text-slate-600">새 계정을 만드세요</p>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Google 회원가입 */}
      <Button
        type="button"
        variant="outline"
        className="w-full mb-6 h-11"
        onClick={handleGoogleSignup}
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

      {/* 회원가입 폼 */}
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
          <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="이름"
            required
            autoComplete="name"
            className="pl-10 h-11"
          />
        </div>

        <div className="relative">
          <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            id="phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="전화번호 (선택)"
            autoComplete="tel"
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
            placeholder="비밀번호 (8자 이상)"
            required
            minLength={8}
            autoComplete="new-password"
            className="pl-10 h-11"
          />
        </div>

        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="비밀번호 확인"
            required
            minLength={8}
            autoComplete="new-password"
            className="pl-10 h-11"
          />
        </div>

        <Button type="submit" className="w-full h-11" disabled={loading}>
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
          ) : (
            "회원가입"
          )}
        </Button>
      </form>

      {/* 개인정보 처리방침 */}
      <p className="mt-4 text-xs text-slate-500 text-center">
        회원가입 시{" "}
        <Link href="/privacy" className="text-primary hover:underline">
          개인정보 처리방침
        </Link>
        에 동의하게 됩니다.
      </p>

      {/* 푸터 */}
      <div className="mt-6 text-center">
        <p className="text-sm text-slate-500">
          이미 계정이 있으신가요?{" "}
          <Link href="/login" className="text-primary font-medium hover:underline">
            로그인
          </Link>
        </p>
      </div>
    </Card>
  );
}

function SignupLoading() {
  return (
    <Card className="w-full max-w-md p-8">
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    </Card>
  );
}

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <Suspense fallback={<SignupLoading />}>
        <SignupForm />
      </Suspense>
    </div>
  );
}
