"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { AlertTriangle, RefreshCw, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function CampaignError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const params = useParams();
  const campaignId = params.campaignId as string;

  useEffect(() => {
    // 에러 로깅
    console.error("Campaign error:", error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <Card className="max-w-md w-full p-8 text-center">
        <div className="mx-auto w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mb-5">
          <AlertTriangle className="h-7 w-7 text-red-600" />
        </div>

        <h2 className="text-xl font-bold text-gray-900 mb-2">
          페이지를 불러올 수 없습니다
        </h2>

        <p className="text-gray-600 mb-6 text-sm">
          캠페인 데이터를 불러오는 중 오류가 발생했습니다.
          <br />
          네트워크 연결을 확인하고 다시 시도해 주세요.
        </p>

        {process.env.NODE_ENV === "development" && (
          <div className="mb-5 p-3 bg-gray-100 rounded-lg text-left">
            <p className="text-xs font-mono text-red-600 break-all">
              {error.message}
            </p>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-2 justify-center">
          <Button onClick={reset} size="sm">
            <RefreshCw className="h-4 w-4 mr-1" />
            다시 시도
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => (window.location.href = "/campaigns")}
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            캠프 목록
          </Button>
        </div>
      </Card>
    </div>
  );
}
