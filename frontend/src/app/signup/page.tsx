"use client";

import { useState, FormEvent, Suspense } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button, Input, Card } from "@/components/ui";
import { APP_NAME } from "@/lib/constants";
import { Shield, Mail, Lock, User, Phone, AlertCircle, Loader2, CheckCircle, X } from "lucide-react";

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
  const [privacyAgreed, setPrivacyAgreed] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // 개인정보 동의 확인
    if (!privacyAgreed) {
      setError("개인정보 제공에 동의해주세요.");
      return;
    }

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
        phone,
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
            placeholder="전화번호"
            required
            autoComplete="tel"
            className="pl-10 h-11"
          />
        </div>

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

        {/* 개인정보 제공 동의 */}
        <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
          <input
            type="checkbox"
            id="privacyAgreed"
            checked={privacyAgreed}
            onChange={(e) => setPrivacyAgreed(e.target.checked)}
            className="mt-1 h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary"
          />
          <label htmlFor="privacyAgreed" className="text-sm text-slate-600">
            <button
              type="button"
              onClick={() => setShowPrivacyModal(true)}
              className="text-primary font-medium hover:underline"
            >
              개인정보 제공 동의
            </button>
            에 동의합니다. (필수)
          </label>
        </div>

        <Button type="submit" className="w-full h-11" disabled={loading || !privacyAgreed}>
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
          ) : (
            "회원가입"
          )}
        </Button>
      </form>

      {/* 개인정보 제공 동의 모달 */}
      {showPrivacyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">개인정보 제공 동의</h3>
              <button
                onClick={() => setShowPrivacyModal(false)}
                className="p-1 hover:bg-slate-100 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1 text-sm text-slate-600 space-y-4">
              <p className="font-medium text-slate-800">1. 수집하는 개인정보 항목</p>
              <p>- 필수항목: 이름, 전화번호, 이메일, 비밀번호</p>

              <p className="font-medium text-slate-800">2. 개인정보의 수집 및 이용 목적</p>
              <p>- 회원 가입 및 관리: 회원제 서비스 이용에 따른 본인확인, 개인 식별, 불량회원의 부정 이용 방지</p>
              <p>- 서비스 제공: 캠프 운영 관리 서비스 제공, 작업/일정/결재 관리 기능 제공</p>
              <p>- 고객 지원: 민원처리, 공지사항 전달</p>

              <p className="font-medium text-slate-800">3. 개인정보의 보유 및 이용 기간</p>
              <p>- 회원 탈퇴 시까지 보유하며, 탈퇴 후 즉시 파기합니다.</p>
              <p>- 단, 관계 법령에 따라 보존할 필요가 있는 경우 해당 기간 동안 보관합니다.</p>

              <p className="font-medium text-slate-800">4. 동의 거부권 및 불이익</p>
              <p>- 귀하는 개인정보 제공에 대한 동의를 거부할 권리가 있습니다.</p>
              <p>- 다만, 필수 항목에 대한 동의를 거부할 경우 회원가입이 제한됩니다.</p>
            </div>
            <div className="p-4 border-t flex gap-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowPrivacyModal(false)}
              >
                닫기
              </Button>
              <Button
                className="flex-1"
                onClick={() => {
                  setPrivacyAgreed(true);
                  setShowPrivacyModal(false);
                }}
              >
                동의하기
              </Button>
            </div>
          </div>
        </div>
      )}

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
