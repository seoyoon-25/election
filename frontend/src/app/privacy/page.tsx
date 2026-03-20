import Link from "next/link";
import { APP_NAME } from "@/lib/constants";
import { Shield, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui";

export const metadata = {
  title: `개인정보 처리방침 - ${APP_NAME}`,
  description: `${APP_NAME} 개인정보 처리방침`,
};

export default function PrivacyPage() {
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
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            개인정보 처리방침
          </h1>
          <p className="text-slate-500 mb-8">최종 수정일: 2024년 1월 1일</p>

          <div className="prose prose-slate max-w-none">
            <p className="text-slate-600 leading-relaxed">
              {APP_NAME}(이하 &quot;서비스&quot;)는 이용자의 개인정보를 중요시하며,
              「개인정보 보호법」을 준수하고 있습니다. 본 개인정보 처리방침은
              서비스 이용 시 수집되는 개인정보의 항목, 수집 목적, 보유 기간 등을
              안내합니다.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              1. 수집하는 개인정보 항목
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              서비스는 다음과 같은 개인정보를 수집합니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>
                <strong>필수 항목:</strong> 이메일 주소, 이름, 비밀번호(암호화 저장)
              </li>
              <li>
                <strong>선택 항목:</strong> 프로필 사진, 연락처
              </li>
              <li>
                <strong>자동 수집:</strong> 접속 로그, IP 주소, 서비스 이용 기록
              </li>
              <li>
                <strong>Google 로그인 시:</strong> Google 계정 이메일, 이름, 프로필 사진
              </li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              2. 개인정보의 수집 및 이용 목적
            </h2>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>회원 가입 및 서비스 이용을 위한 본인 확인</li>
              <li>선거 캠프 팀원 간 협업 기능 제공</li>
              <li>업무 관리, 일정 공유, 결재 워크플로우 기능 제공</li>
              <li>서비스 관련 공지사항 전달</li>
              <li>서비스 개선 및 통계 분석</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              3. 개인정보의 보유 및 이용 기간
            </h2>
            <p className="text-slate-600 leading-relaxed">
              이용자의 개인정보는 서비스 이용 기간 동안 보유하며, 회원 탈퇴 시
              지체 없이 파기합니다. 단, 관계 법령에 따라 보존할 필요가 있는 경우
              해당 기간 동안 보관합니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mt-4">
              <li>계약 또는 청약철회 등에 관한 기록: 5년</li>
              <li>대금결제 및 재화 등의 공급에 관한 기록: 5년</li>
              <li>소비자 불만 또는 분쟁처리에 관한 기록: 3년</li>
              <li>접속 로그: 3개월</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              4. 개인정보의 제3자 제공
            </h2>
            <p className="text-slate-600 leading-relaxed">
              서비스는 이용자의 개인정보를 원칙적으로 외부에 제공하지 않습니다.
              다만, 다음의 경우에는 예외로 합니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mt-4">
              <li>이용자가 사전에 동의한 경우</li>
              <li>법령의 규정에 의거하거나, 수사 목적으로 법령에 정해진 절차와 방법에 따라 수사기관의 요구가 있는 경우</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              5. 개인정보의 파기
            </h2>
            <p className="text-slate-600 leading-relaxed">
              서비스는 개인정보 보유 기간의 경과, 처리 목적 달성 등 개인정보가
              불필요하게 되었을 때에는 지체 없이 해당 개인정보를 파기합니다.
              전자적 파일 형태의 정보는 복구할 수 없는 방법으로 영구 삭제하며,
              종이에 출력된 개인정보는 분쇄하거나 소각하여 파기합니다.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              6. 이용자의 권리
            </h2>
            <p className="text-slate-600 leading-relaxed">
              이용자는 언제든지 자신의 개인정보를 조회하거나 수정할 수 있으며,
              회원 탈퇴를 통해 개인정보의 삭제를 요청할 수 있습니다.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              7. 개인정보 보호책임자
            </h2>
            <p className="text-slate-600 leading-relaxed">
              서비스는 개인정보 처리에 관한 업무를 총괄해서 책임지고, 개인정보
              처리와 관련한 이용자의 불만처리 및 피해구제 등을 위하여 아래와 같이
              개인정보 보호책임자를 지정하고 있습니다.
            </p>
            <div className="bg-slate-50 rounded-lg p-4 mt-4">
              <p className="text-slate-600">
                <strong>개인정보 보호책임자</strong>
                <br />
                이메일: privacy@bestcome.org
              </p>
            </div>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              8. 개인정보 처리방침의 변경
            </h2>
            <p className="text-slate-600 leading-relaxed">
              이 개인정보 처리방침은 법령, 정책 또는 보안기술의 변경에 따라
              내용의 추가, 삭제 및 수정이 있을 수 있으며, 변경 시 서비스 내
              공지사항을 통해 고지합니다.
            </p>
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
