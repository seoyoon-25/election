"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, CardTitle, Button, Input } from "@/components/ui";
import { Header } from "@/components/layout";
import { ArrowLeft, Building2, Loader2 } from "lucide-react";

const ELECTION_TYPES = [
  { value: "president", label: "대통령 선거" },
  { value: "governor", label: "시/도지사 선거" },
  { value: "mayor", label: "시장/군수/구청장 선거" },
  { value: "assembly", label: "국회의원 선거" },
  { value: "council", label: "시/도의회 의원 선거" },
  { value: "education", label: "교육감 선거" },
  { value: "other", label: "기타" },
];

interface CampaignCreateResponse {
  id: number;
  name: string;
  slug: string;
}

export default function NewCampaignPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [electionType, setElectionType] = useState("");
  const [electionDate, setElectionDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("캠프 이름을 입력하세요");
      return;
    }

    if (!electionType) {
      setError("선거 종류를 선택하세요");
      return;
    }

    setLoading(true);

    try {
      const response = await api.post<CampaignCreateResponse>("/campaigns", {
        name: name.trim(),
        description: ELECTION_TYPES.find(t => t.value === electionType)?.label || "",
        end_date: electionDate || null,
        timezone: "Asia/Seoul",
      });

      // 캠프 생성 후 대시보드로 이동
      router.push(`/c/${response.id}/dashboard`);
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes("409")) {
          setError("이미 사용 중인 캠프 이름입니다");
        } else {
          setError(err.message);
        }
      } else {
        setError("캠프 생성에 실패했습니다");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-xl mx-auto py-8 px-4">
        <div className="mb-6">
          <Link
            href="/campaigns"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            돌아가기
          </Link>
        </div>

        <Card padding="lg">
          <div className="text-center mb-6">
            <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Building2 className="w-6 h-6 text-primary" />
            </div>
            <CardTitle>새 캠프 만들기</CardTitle>
            <p className="text-gray-600 mt-1">
              선거 캠프 정보를 입력하세요
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                캠프 이름 <span className="text-red-500">*</span>
              </label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="예: 홍길동 후보 캠프"
                required
              />
            </div>

            <div>
              <label
                htmlFor="electionType"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                선거 종류 <span className="text-red-500">*</span>
              </label>
              <select
                id="electionType"
                value={electionType}
                onChange={(e) => setElectionType(e.target.value)}
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                required
              >
                <option value="">선택하세요</option>
                {ELECTION_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="electionDate"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                선거일
              </label>
              <Input
                id="electionDate"
                type="date"
                value={electionDate}
                onChange={(e) => setElectionDate(e.target.value)}
              />
              <p className="text-xs text-gray-500 mt-1">
                선거일까지 남은 D-Day가 대시보드에 표시됩니다
              </p>
            </div>

            <div className="pt-4">
              <Button
                type="submit"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    생성 중...
                  </>
                ) : (
                  "캠프 만들기"
                )}
              </Button>
            </div>
          </form>
        </Card>
      </main>
    </div>
  );
}
