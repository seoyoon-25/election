import Link from "next/link";
import type { Metadata } from "next";
import {
  CheckCircle2,
  Calendar,
  Users,
  ClipboardList,
  Shield,
} from "lucide-react";
import { GoogleLoginButton, EmailLoginButton } from "@/components/landing/LoginButtons";

// SEO를 위한 메타데이터
export const metadata: Metadata = {
  title: "캠프보드 - 선거 캠프 운영 관리 시스템",
  description: "캠프보드는 선거 캠프를 위한 업무 관리 시스템입니다. 업무 관리(칸반 보드), 일정 공유, 결재 워크플로우, 팀원 관리 기능을 제공합니다.",
  keywords: ["캠프보드", "선거", "캠프", "업무관리", "태스크", "협업", "선거캠프"],
  openGraph: {
    title: "캠프보드 - 선거 캠프 운영 관리 시스템",
    description: "캠프보드는 선거 캠프를 위한 업무 관리 시스템입니다.",
    siteName: "캠프보드",
  },
};

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
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* 헤더 */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-slate-900">캠프보드</span>
          </div>
          <nav className="flex items-center gap-4">
            <Link
              href="/privacy"
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              개인정보처리방침
            </Link>
            <Link href="/login">
              <span className="text-sm font-medium text-primary hover:text-primary/80">
                회원가입/로그인
              </span>
            </Link>
          </nav>
        </div>
      </header>

      {/* 히어로 섹션 */}
      <section className="py-24 px-4">
        <div className="max-w-3xl mx-auto text-center">
          {/* 앱 이름과 설명 배지 */}
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full mb-6">
            <Shield className="w-4 h-4" />
            <span className="font-bold">캠프보드</span>
            <span className="text-primary/70">| 선거 캠프 운영 관리 시스템</span>
          </div>

          {/* 메인 타이틀 - 앱 이름 명시 */}
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 leading-tight tracking-tight">
            <span className="text-primary">캠프보드</span>로
            <br />
            선거캠프를 관리하세요
          </h1>

          {/* 앱 목적 설명 - 명확하게 */}
          <div className="bg-slate-100 rounded-xl p-6 mb-8 max-w-2xl mx-auto">
            <h2 className="text-lg font-semibold text-slate-800 mb-2">
              캠프보드란?
            </h2>
            <p className="text-slate-600 leading-relaxed">
              <strong>캠프보드</strong>는 <strong>선거 캠프를 위한 업무 관리 시스템</strong>입니다.
              업무 관리(칸반 보드), 일정 공유, 결재 워크플로우, 팀원 관리 등
              캠프 운영에 필요한 모든 기능을 하나의 공간에서 제공합니다.
            </p>
          </div>

          {/* CTA 버튼들 - 클라이언트 컴포넌트 */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
            <GoogleLoginButton />
            <EmailLoginButton />
          </div>

          <p className="mt-6 text-sm text-slate-500">
            초대받은 팀원만 가입할 수 있습니다
          </p>

          {/* 개인정보처리방침 및 이용약관 링크 */}
          <div className="mt-4 flex justify-center gap-4 text-sm">
            <Link href="/privacy" className="text-primary hover:underline font-medium">
              개인정보 처리방침
            </Link>
            <span className="text-slate-300">|</span>
            <Link href="/terms" className="text-slate-500 hover:text-slate-700">
              이용약관
            </Link>
          </div>
        </div>
      </section>

      {/* 기능 소개 - 간결한 그리드 */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center text-slate-900 mb-8">
            캠프보드 주요 기능
          </h2>
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
            <span className="font-semibold text-slate-700">캠프보드</span>
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
            <nav className="flex gap-4 sm:gap-6 text-sm text-slate-500">
              <Link href="/privacy" className="hover:text-slate-700 font-medium">
                개인정보 처리방침
              </Link>
              <Link href="/terms" className="hover:text-slate-700">
                이용약관
              </Link>
              <Link href="/app-terms" className="hover:text-slate-700">
                앱 서비스 약관
              </Link>
            </nav>
            <p className="text-sm text-slate-500">
              &copy; 2024 캠프보드
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
