"use client";

import { useState, FormEvent, Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button, Input, Card } from "@/components/ui";
import { APP_NAME } from "@/lib/constants";
import { Shield, Lock, AlertCircle, Loader2, CheckCircle } from "lucide-react";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [invalidToken, setInvalidToken] = useState(false);

  useEffect(() => {
    const tokenParam = searchParams.get("token");
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setInvalidToken(true);
    }
  }, [searchParams]);

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
      await api.post("/auth/password/reset-confirm", {
        token,
        new_password: password,
      });
      setSuccess(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "비밀번호 재설정에 실패했습니다";
      if (errorMessage.toLowerCase().includes("invalid") || errorMessage.toLowerCase().includes("expired")) {
        setError("유효하지 않거나 만료된 링크입니다. 비밀번호 찾기를 다시 시도해주세요.");
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  if (invalidToken) {
    return (
      <Card className="w-full max-w-md p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2">잘못된 접근</h2>
          <p className="text-slate-600 mb-6">
            유효하지 않은 비밀번호 재설정 링크입니다.<br />
            이메일의 링크를 다시 확인해주세요.
          </p>
          <Link href="/forgot-password">
            <Button className="w-full">비밀번호 찾기</Button>
          </Link>
        </div>
      </Card>
    );
  }

  if (success) {
    return (
      <Card className="w-full max-w-md p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2">비밀번호 변경 완료</h2>
          <p className="text-slate-600 mb-6">
            비밀번호가 성공적으로 변경되었습니다.<br />
            새 비밀번호로 로그인하세요.
          </p>
          <Link href="/login">
            <Button className="w-full">로그인하기</Button>
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
        <h2 className="text-xl font-semibold mb-2">새 비밀번호 설정</h2>
        <p className="text-slate-600">
          새로운 비밀번호를 입력하세요.
        </p>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* 비밀번호 설정 폼 */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="새 비밀번호 (8자 이상)"
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
            "비밀번호 변경"
          )}
        </Button>
      </form>

      {/* 푸터 */}
      <div className="mt-6 text-center">
        <p className="text-sm text-slate-500">
          <Link href="/login" className="text-primary font-medium hover:underline">
            로그인으로 돌아가기
          </Link>
        </p>
      </div>
    </Card>
  );
}

function ResetPasswordLoading() {
  return (
    <Card className="w-full max-w-md p-8">
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <Suspense fallback={<ResetPasswordLoading />}>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
