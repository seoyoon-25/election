"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, CardTitle, Button, Input } from "@/components/ui";
import { Header } from "@/components/layout";
import { ArrowLeft, Building2, Loader2 } from "lucide-react";

// 선거 종류 카테고리 구조
const ELECTION_CATEGORIES = [
  {
    category: "광역단체장",
    types: [
      { value: "metropolitan_governor", label: "시·도지사", example: "서울시장, 경기도지사 등" },
      { value: "superintendent", label: "교육감", example: "" },
    ],
  },
  {
    category: "기초단체장",
    types: [
      { value: "mayor", label: "시장", example: "" },
      { value: "county_head", label: "군수", example: "" },
      { value: "district_head", label: "구청장", example: "" },
    ],
  },
  {
    category: "의회",
    types: [
      { value: "national_assembly", label: "국회의원", example: "" },
      { value: "metropolitan_council", label: "시·도의회의원", example: "" },
      { value: "local_council", label: "시·군·구의회의원", example: "" },
    ],
  },
  {
    category: "대통령",
    types: [
      { value: "president", label: "대통령", example: "" },
    ],
  },
  {
    category: "기타",
    types: [
      { value: "other", label: "기타", example: "" },
    ],
  },
];

// 지역 목록
const REGIONS = [
  "서울특별시",
  "부산광역시",
  "대구광역시",
  "인천광역시",
  "광주광역시",
  "대전광역시",
  "울산광역시",
  "세종특별자치시",
  "경기도",
  "강원특별자치도",
  "충청북도",
  "충청남도",
  "전라북도",
  "전라남도",
  "경상북도",
  "경상남도",
  "제주특별자치도",
];

interface CampaignCreateResponse {
  id: number;
  name: string;
  slug: string;
}

export default function NewCampaignPage() {
  const router = useRouter();
  const [candidateName, setCandidateName] = useState("");
  const [campName, setCampName] = useState("");
  const [campNameManuallyEdited, setCampNameManuallyEdited] = useState(false);
  const [electionType, setElectionType] = useState("");
  const [electionDate, setElectionDate] = useState("");
  const [region, setRegion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 후보자 이름 변경 시 캠프 이름 자동 생성
  useEffect(() => {
    if (!campNameManuallyEdited && candidateName.trim()) {
      setCampName(`${candidateName.trim()} 캠프`);
    } else if (!campNameManuallyEdited && !candidateName.trim()) {
      setCampName("");
    }
  }, [candidateName, campNameManuallyEdited]);

  // 캠프 이름 수동 변경 감지
  const handleCampNameChange = (value: string) => {
    setCampName(value);
    setCampNameManuallyEdited(true);
  };

  // 선택된 선거 종류의 라벨 가져오기
  const getElectionTypeLabel = (value: string): string => {
    for (const category of ELECTION_CATEGORIES) {
      const found = category.types.find(t => t.value === value);
      if (found) return found.label;
    }
    return "";
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (!candidateName.trim()) {
      setError("후보자 이름을 입력하세요");
      return;
    }

    if (!campName.trim()) {
      setError("캠프 이름을 입력하세요");
      return;
    }

    if (!electionType) {
      setError("선거 종류를 선택하세요");
      return;
    }

    setLoading(true);

    try {
      // description에 선거 종류와 지역 정보를 저장
      const electionLabel = getElectionTypeLabel(electionType);
      const description = region
        ? `${region} ${electionLabel}`
        : electionLabel;

      const response = await api.post<CampaignCreateResponse>("/campaigns", {
        name: campName.trim(),
        description,
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
            {/* 후보자 이름 */}
            <div>
              <label
                htmlFor="candidateName"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                후보자 이름 <span className="text-red-500">*</span>
              </label>
              <Input
                id="candidateName"
                type="text"
                value={candidateName}
                onChange={(e) => setCandidateName(e.target.value)}
                placeholder="예: 홍길동"
                required
              />
            </div>

            {/* 캠프 이름 */}
            <div>
              <label
                htmlFor="campName"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                캠프 이름 <span className="text-red-500">*</span>
              </label>
              <Input
                id="campName"
                type="text"
                value={campName}
                onChange={(e) => handleCampNameChange(e.target.value)}
                placeholder="예: 홍길동 캠프"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                후보자 이름 입력 시 자동으로 생성됩니다
              </p>
            </div>

            {/* 선거 종류 (그룹핑된 select) */}
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
                {ELECTION_CATEGORIES.map((category) => (
                  <optgroup key={category.category} label={category.category}>
                    {category.types.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                        {type.example && ` (${type.example})`}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>

            {/* 선거 지역 */}
            <div>
              <label
                htmlFor="region"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                선거 지역
              </label>
              <select
                id="region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <option value="">선택하세요 (선택 사항)</option>
                {REGIONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            {/* 선거일 */}
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
