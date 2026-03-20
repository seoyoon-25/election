import Link from "next/link";
import { APP_NAME } from "@/lib/constants";
import { Shield, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui";

export const metadata = {
  title: `이용약관 - ${APP_NAME}`,
  description: `${APP_NAME} 서비스 이용약관`,
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* 헤더 */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-slate-900">{APP_NAME}</span>
          </Link>
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              돌아가기
            </Button>
          </Link>
        </div>
      </header>

      {/* 본문 */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-xl border p-8 md:p-12">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">이용약관</h1>
          <p className="text-slate-500 mb-8">최종 수정일: 2024년 1월 1일</p>

          <div className="prose prose-slate max-w-none">
            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제1조 (목적)
            </h2>
            <p className="text-slate-600 leading-relaxed">
              이 약관은 {APP_NAME}(이하 &quot;서비스&quot;)가 제공하는 선거 캠프 운영 관리
              서비스의 이용과 관련하여 서비스와 이용자 간의 권리, 의무 및
              책임사항 등을 규정함을 목적으로 합니다.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제2조 (정의)
            </h2>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>
                <strong>&quot;서비스&quot;</strong>란 선거 캠프의 업무 관리, 일정 공유,
                결재 워크플로우, 팀원 관리 등을 지원하는 웹 기반 협업 플랫폼을
                의미합니다.
              </li>
              <li>
                <strong>&quot;이용자&quot;</strong>란 이 약관에 따라 서비스에 접속하여
                서비스를 이용하는 회원을 말합니다.
              </li>
              <li>
                <strong>&quot;캠페인&quot;</strong>이란 서비스 내에서 생성된 개별 선거 캠프
                운영 단위를 의미합니다.
              </li>
              <li>
                <strong>&quot;초대&quot;</strong>란 기존 캠페인 관리자가 새로운 팀원을
                서비스에 가입시키기 위해 발송하는 이메일 초대를 의미합니다.
              </li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제3조 (이용계약의 체결)
            </h2>
            <ol className="list-decimal pl-6 text-slate-600 space-y-2">
              <li>
                이용계약은 캠페인 관리자의 초대를 받은 자가 초대를 수락하고
                회원가입을 완료함으로써 체결됩니다.
              </li>
              <li>
                서비스는 초대 기반 가입 시스템으로 운영되며, 초대 없이는 회원가입이
                불가능합니다.
              </li>
              <li>
                이용자는 회원가입 시 정확한 정보를 제공해야 하며, 허위 정보 제공
                시 서비스 이용이 제한될 수 있습니다.
              </li>
            </ol>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제4조 (서비스의 제공)
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              서비스는 다음과 같은 기능을 제공합니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>업무(태스크) 관리 및 칸반 보드</li>
              <li>일정 및 캘린더 관리</li>
              <li>결재 요청 및 승인 워크플로우</li>
              <li>팀원 및 부서 관리</li>
              <li>역할 기반 접근 제어(RBAC)</li>
              <li>기타 선거 캠프 운영에 필요한 협업 기능</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제5조 (이용자의 의무)
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              이용자는 다음 행위를 하여서는 안 됩니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>타인의 정보 도용</li>
              <li>서비스 운영을 방해하는 행위</li>
              <li>다른 이용자의 개인정보를 무단 수집하는 행위</li>
              <li>서비스를 이용하여 법령에 위반되는 행위</li>
              <li>서비스의 보안을 위협하는 행위</li>
              <li>공직선거법 등 관계 법령을 위반하는 행위</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제6조 (역할 및 권한)
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              서비스는 역할 기반 접근 제어 시스템을 운영합니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>
                <strong>캠프 대표(Owner):</strong> 캠페인의 모든 권한을 가지며,
                다른 관리자를 지정할 수 있습니다.
              </li>
              <li>
                <strong>관리자(Admin):</strong> 팀원 초대, 역할 변경 등 관리
                기능을 수행합니다.
              </li>
              <li>
                <strong>부서장:</strong> 담당 부서의 업무를 관리합니다.
              </li>
              <li>
                <strong>팀원:</strong> 할당된 업무를 수행하고 일정을 확인합니다.
              </li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제7조 (서비스의 변경 및 중단)
            </h2>
            <ol className="list-decimal pl-6 text-slate-600 space-y-2">
              <li>
                서비스는 운영상, 기술상의 필요에 따라 서비스의 전부 또는 일부를
                변경할 수 있습니다.
              </li>
              <li>
                서비스는 시스템 점검, 장비 교체 등 불가피한 사유가 있는 경우
                서비스 제공을 일시적으로 중단할 수 있습니다.
              </li>
              <li>
                서비스 중단 시 사전에 공지하며, 불가피한 경우 사후에 공지할 수
                있습니다.
              </li>
            </ol>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제8조 (책임의 제한)
            </h2>
            <ol className="list-decimal pl-6 text-slate-600 space-y-2">
              <li>
                서비스는 천재지변, 전쟁, 기간통신사업자의 서비스 중단 등
                불가항력으로 인하여 서비스를 제공할 수 없는 경우 책임을 면합니다.
              </li>
              <li>
                서비스는 이용자의 귀책사유로 인한 서비스 이용 장애에 대해 책임을
                지지 않습니다.
              </li>
              <li>
                서비스에 게재된 정보의 신뢰도, 정확성에 대해서는 이용자가 스스로
                판단하여야 합니다.
              </li>
            </ol>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제9조 (분쟁해결)
            </h2>
            <ol className="list-decimal pl-6 text-slate-600 space-y-2">
              <li>
                서비스와 이용자 간에 발생한 분쟁에 대해 이용자가 이의를 제기할
                경우 서비스는 이용자의 의견을 적극 수렴하여 해결하도록 합니다.
              </li>
              <li>
                이 약관과 관련하여 발생하는 분쟁에 대해서는 대한민국 법률을
                적용하며, 관할법원은 서비스 제공자의 소재지 관할 법원으로 합니다.
              </li>
            </ol>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              제10조 (약관의 변경)
            </h2>
            <p className="text-slate-600 leading-relaxed">
              서비스는 필요한 경우 약관을 변경할 수 있으며, 변경된 약관은 적용일
              7일 전에 공지합니다. 이용자가 변경된 약관에 동의하지 않을 경우
              서비스 이용을 중단하고 탈퇴할 수 있습니다.
            </p>

            <div className="bg-slate-50 rounded-lg p-4 mt-8">
              <p className="text-slate-600">
                <strong>부칙</strong>
                <br />이 약관은 2024년 1월 1일부터 시행합니다.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* 푸터 */}
      <footer className="py-8 px-4 border-t bg-white">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-semibold text-slate-700">{APP_NAME}</span>
          </div>
          <div className="flex gap-4 sm:gap-6 text-sm text-slate-500">
            <Link href="/privacy" className="hover:text-slate-700">
              개인정보 처리방침
            </Link>
            <Link href="/terms" className="hover:text-slate-700">
              이용약관
            </Link>
            <Link href="/app-terms" className="hover:text-slate-700">
              앱 서비스 약관
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
