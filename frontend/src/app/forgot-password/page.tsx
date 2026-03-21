"use client";

import { useState, FormEvent, Suspense } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button, Input, Card } from "@/components/ui";
import { APP_NAME } from "@/lib/constants";
import { Shield, Mail, AlertCircle, Loader2, CheckCircle, ArrowLeft } from "lucide-react";

function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.post("/auth/password/reset-request", { email });
      setSuccess(true);
    } catch (err) {
      // 보안상 항상 성공 메시지를 표시 (이메일 존재 여부 노출 방지)
      setSuccess(true);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Card className="w-full max-w-md p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2">이메일을 확인하세요</h2>
          <p className="text-slate-600 mb-6">
            <span className="font-medium">{email}</span>로<br />
            비밀번호 재설정 링크를 발송했습니다.
          </p>
          <p className="text-sm text-slate-500 mb-6">
            이메일이 도착하지 않으면 스팸 폴더를 확인해주세요.
          </p>
          <Link href="/login">
            <Button variant="outline" className="w-full">
              <ArrowLeft className="w-4 h-4 mr-2" />
              로그인으로 돌아가기
            </Button>
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
        <h2 className="text-xl font-semibold mb-2">비밀번호 찾기</h2>
        <p className="text-slate-600">
          가입한 이메일을 입력하시면<br />
          비밀번호 재설정 링크를 보내드립니다.
        </p>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* 이메일 입력 폼 */}
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

        <Button type="submit" className="w-full h-11" disabled={loading}>
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
          ) : (
            "재설정 링크 받기"
          )}
        </Button>
      </form>

      {/* 푸터 */}
      <div className="mt-6 text-center">
        <Link
          href="/login"
          className="text-sm text-slate-500 hover:text-slate-700 inline-flex items-center gap-1"
        >
          <ArrowLeft className="w-4 h-4" />
          로그인으로 돌아가기
        </Link>
      </div>
    </Card>
  );
}

function ForgotPasswordLoading() {
  return (
    <Card className="w-full max-w-md p-8">
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    </Card>
  );
}

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <Suspense fallback={<ForgotPasswordLoading />}>
        <ForgotPasswordForm />
      </Suspense>
    </div>
  );
}
