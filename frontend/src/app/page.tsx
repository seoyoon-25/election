"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { isAuthenticated } from "@/lib/auth";
import { api } from "@/lib/api";
import { APP_NAME } from "@/lib/constants";
import { Button } from "@/components/ui";
import {
  CheckCircle2,
  Calendar,
  Users,
  ClipboardList,
  Shield,
  Loader2,
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

const FEATURES = [
  {
    icon: ClipboardList,
    title: "업무 관리",
    description: "칸반 보드로 팀 업무를 한눈에",
  },
  {
    icon: Calendar,
    title: "일정 공유",
    description: "유세/회의/마감일 함께 관리",
  },
  {
    icon: Users,
    title: "팀 협업",
    description: "역할별 권한으로 효율적 협업",
  },
  {
    icon: CheckCircle2,
    title: "결재 워크플로우",
    description: "체계적인 승인 프로세스",
  },
];

export default function LandingPage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      router.push("/campaigns");
    } else {
      setChecking(false);
    }
  }, [router]);

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      const response = await api.get<{ authorization_url: string }>(
        "/auth/google?redirect_uri=/login"
      );
      window.location.href = response.authorization_url;
    } catch {
      router.push("/login");
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* 헤더 */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-slate-900">{APP_NAME}</span>
          </div>
          <Link href="/login">
            <Button variant="ghost" size="sm">
              로그인
            </Button>
          </Link>
        </div>
      </header>

      {/* 히어로 섹션 */}
      <section className="py-24 px-4">
        <div className="max-w-3xl mx-auto text-center">
          {/* 메인 타이틀 */}
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 leading-tight tracking-tight">
            선거캠프 실무를
            <br />
            <span className="text-primary">한곳에서</span> 관리하세요
          </h1>

          {/* 서브 설명 */}
          <p className="text-lg md:text-xl text-slate-600 mb-10 max-w-xl mx-auto leading-relaxed">
            업무, 일정, 결재, 팀원 관리까지
            <br className="hidden sm:block" />
            캠프 운영에 필요한 모든 것을 하나의 공간에서
          </p>

          {/* CTA 버튼들 */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
            <Button
              size="lg"
              variant="outline"
              className="w-full sm:w-auto h-12 px-6 text-base"
              onClick={handleGoogleLogin}
              disabled={googleLoading}
            >
              {googleLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <GoogleIcon className="w-5 h-5 mr-2" />
                  Google로 시작하기
                </>
              )}
            </Button>
            <Link href="/login">
              <Button
                size="lg"
                className="w-full sm:w-auto h-12 px-6 text-base"
              >
                이메일로 로그인
              </Button>
            </Link>
          </div>

          <p className="mt-6 text-sm text-slate-500">
            초대받은 팀원만 가입할 수 있습니다
          </p>
        </div>
      </section>

      {/* 기능 소개 - 간결한 그리드 */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="text-center p-5 rounded-xl bg-white border border-slate-100 shadow-sm"
              >
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-semibold text-slate-900 mb-1">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-500">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 신뢰 배지 섹션 */}
      <section className="py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="bg-slate-900 rounded-2xl p-8 md:p-12 text-center">
            <h2 className="text-xl md:text-2xl font-bold text-white mb-3">
              체계적인 캠프 운영의 시작
            </h2>
            <p className="text-slate-400 mb-6">
              역할별 권한 관리로 안전하고 효율적인 협업 환경
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              {["관리자", "총무", "정책", "홍보", "스태프"].map((role) => (
                <span
                  key={role}
                  className="px-4 py-2 bg-white/10 text-white/90 rounded-full text-sm font-medium"
                >
                  {role}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 푸터 */}
      <footer className="py-8 px-4 border-t bg-white">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-semibold text-slate-700">{APP_NAME}</span>
          </div>
          <p className="text-sm text-slate-500">
            &copy; 2024 {APP_NAME}. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
