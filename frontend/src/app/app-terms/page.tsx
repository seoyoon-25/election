import Link from "next/link";
import { APP_NAME } from "@/lib/constants";
import { Shield, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui";

export const metadata = {
  title: `애플리케이션 서비스 약관 - ${APP_NAME}`,
  description: `${APP_NAME} 애플리케이션 서비스 약관`,
};

export default function AppTermsPage() {
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
            애플리케이션 서비스 약관
          </h1>
          <p className="text-slate-500 mb-8">최종 수정일: 2024년 1월 1일</p>

          <div className="prose prose-slate max-w-none">
            <p className="text-slate-600 leading-relaxed">
              본 애플리케이션 서비스 약관은 {APP_NAME}(이하 &quot;앱&quot;)이 Google 및
              기타 제3자 서비스와 연동하여 제공하는 기능에 대한 이용 조건을
              규정합니다.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              1. Google 서비스 연동
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              앱은 다음과 같은 Google 서비스와 연동됩니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>
                <strong>Google 로그인 (OAuth 2.0):</strong> 사용자 인증을 위해
                Google 계정 정보(이메일, 이름, 프로필 사진)에 접근합니다.
              </li>
              <li>
                <strong>Google Calendar API:</strong> 일정 동기화를 위해 사용자의
                캘린더 정보에 접근할 수 있습니다 (선택적 기능).
              </li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              2. Google 사용자 데이터 사용
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              앱이 Google로부터 수신하는 데이터의 사용 및 다른 앱으로의 전송은{" "}
              <a
                href="https://developers.google.com/terms/api-services-user-data-policy"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Google API 서비스 사용자 데이터 정책
              </a>
              (제한적 사용 요구사항 포함)을 준수합니다.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
              <p className="text-slate-700 text-sm">
                <strong>Google Limited Use Disclosure:</strong>
                <br />
                {APP_NAME}&apos;s use and transfer to any other app of information
                received from Google APIs will adhere to{" "}
                <a
                  href="https://developers.google.com/terms/api-services-user-data-policy#additional_requirements_for_specific_api_scopes"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Google API Services User Data Policy
                </a>
                , including the Limited Use requirements.
              </p>
            </div>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              3. 데이터 접근 범위
            </h2>
            <p className="text-slate-600 leading-relaxed mb-4">
              앱은 다음 범위의 Google 데이터에 접근합니다:
            </p>
            <table className="w-full border-collapse border border-slate-200 mt-4">
              <thead>
                <tr className="bg-slate-50">
                  <th className="border border-slate-200 px-4 py-2 text-left text-sm font-semibold text-slate-700">
                    범위 (Scope)
                  </th>
                  <th className="border border-slate-200 px-4 py-2 text-left text-sm font-semibold text-slate-700">
                    용도
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border border-slate-200 px-4 py-2 text-sm text-slate-600">
                    openid
                  </td>
                  <td className="border border-slate-200 px-4 py-2 text-sm text-slate-600">
                    사용자 인증
                  </td>
                </tr>
                <tr>
                  <td className="border border-slate-200 px-4 py-2 text-sm text-slate-600">
                    email
                  </td>
                  <td className="border border-slate-200 px-4 py-2 text-sm text-slate-600">
                    이메일 주소 확인 및 계정 연동
                  </td>
                </tr>
                <tr>
                  <td className="border border-slate-200 px-4 py-2 text-sm text-slate-600">
                    profile
                  </td>
                  <td className="border border-slate-200 px-4 py-2 text-sm text-slate-600">
                    이름, 프로필 사진 표시
                  </td>
                </tr>
              </tbody>
            </table>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              4. 데이터 저장 및 보안
            </h2>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>
                Google로부터 받은 인증 토큰은 암호화되어 안전하게 저장됩니다.
              </li>
              <li>
                사용자 데이터는 서비스 제공 목적으로만 사용되며, 제3자에게
                판매하거나 공유하지 않습니다.
              </li>
              <li>
                모든 데이터 전송은 HTTPS를 통해 암호화됩니다.
              </li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              5. 데이터 삭제
            </h2>
            <p className="text-slate-600 leading-relaxed">
              사용자는 언제든지 다음 방법으로 데이터 삭제를 요청할 수 있습니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mt-4">
              <li>서비스 내 계정 설정에서 회원 탈퇴</li>
              <li>
                <a
                  href="https://myaccount.google.com/permissions"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Google 계정 권한 관리
                </a>
                에서 앱 접근 권한 해제
              </li>
              <li>privacy@bestcome.org로 삭제 요청 이메일 발송</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              6. 제3자 서비스
            </h2>
            <p className="text-slate-600 leading-relaxed">
              앱은 서비스 제공을 위해 다음 제3자 서비스를 사용합니다:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mt-4">
              <li>
                <strong>Google Cloud Platform:</strong> 인증 및 API 서비스
              </li>
              <li>
                <strong>Cloudflare:</strong> CDN 및 보안 서비스
              </li>
            </ul>
            <p className="text-slate-600 leading-relaxed mt-4">
              각 서비스의 이용약관 및 개인정보처리방침은 해당 서비스 제공자의
              정책을 따릅니다.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              7. 서비스 변경 및 중단
            </h2>
            <p className="text-slate-600 leading-relaxed">
              제3자 API 서비스의 정책 변경, 서비스 중단 등의 사유로 앱의 일부
              기능이 변경되거나 중단될 수 있습니다. 이 경우 사전에 공지하며,
              불가피한 경우 사후에 공지할 수 있습니다.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              8. 문의
            </h2>
            <p className="text-slate-600 leading-relaxed">
              본 약관 또는 Google 서비스 연동과 관련하여 문의사항이 있으시면
              아래로 연락해 주세요.
            </p>
            <div className="bg-slate-50 rounded-lg p-4 mt-4">
              <p className="text-slate-600">
                <strong>이메일:</strong> support@bestcome.org
                <br />
                <strong>개인정보 관련:</strong> privacy@bestcome.org
              </p>
            </div>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">
              9. 관련 문서
            </h2>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>
                <Link href="/privacy" className="text-primary hover:underline">
                  개인정보 처리방침
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-primary hover:underline">
                  서비스 이용약관
                </Link>
              </li>
            </ul>
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
          <div className="flex gap-6 text-sm text-slate-500">
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
