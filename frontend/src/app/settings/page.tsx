"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { APP_NAME } from "@/lib/constants";
import {
  Button,
  Input,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui";
import {
  Shield,
  Lock,
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  ArrowLeft,
  Loader2,
} from "lucide-react";

type FormStatus = "idle" | "loading" | "success" | "error";

export default function SettingsPage() {
  const router = useRouter();

  // Form state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Visibility toggles
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // Status
  const [status, setStatus] = useState<FormStatus>("idle");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const validateForm = (): string | null => {
    if (!currentPassword) {
      return "현재 비밀번호를 입력하세요";
    }
    if (newPassword.length < 8) {
      return "새 비밀번호는 8자 이상이어야 합니다";
    }
    if (newPassword !== confirmPassword) {
      return "새 비밀번호가 일치하지 않습니다";
    }
    if (currentPassword === newPassword) {
      return "새 비밀번호는 현재 비밀번호와 달라야 합니다";
    }
    return null;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setStatus("loading");

    try {
      await api.post("/auth/password/change", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      setStatus("success");
      setSuccessMessage("비밀번호가 변경되었습니다");

      // Reset form
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      // Reset status after 3 seconds
      setTimeout(() => {
        setStatus("idle");
        setSuccessMessage("");
      }, 3000);
    } catch (err) {
      setStatus("error");
      if (err instanceof Error) {
        // Handle specific error messages
        if (err.message.includes("incorrect") || err.message.includes("wrong")) {
          setError("현재 비밀번호가 올바르지 않습니다");
        } else {
          setError(err.message || "비밀번호 변경에 실패했습니다");
        }
      } else {
        setError("비밀번호 변경에 실패했습니다");
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-12 px-4">
      <div className="max-w-lg mx-auto">
        {/* 헤더 */}
        <div className="mb-8">
          <Link
            href="/campaigns"
            className="inline-flex items-center text-sm text-slate-600 hover:text-slate-900 mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            돌아가기
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">계정 설정</h1>
              <p className="text-sm text-slate-600">{APP_NAME}</p>
            </div>
          </div>
        </div>

        {/* 비밀번호 변경 카드 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="w-5 h-5" />
              비밀번호 변경
            </CardTitle>
            <CardDescription>
              계정 보안을 위해 주기적으로 비밀번호를 변경하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* 성공 메시지 */}
            {status === "success" && successMessage && (
              <div className="mb-6 p-4 rounded-lg bg-green-50 border border-green-200 flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
                <p className="text-sm text-green-700">{successMessage}</p>
              </div>
            )}

            {/* 에러 메시지 */}
            {error && (
              <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* 현재 비밀번호 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  현재 비밀번호
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    type={showCurrent ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="현재 비밀번호 입력"
                    required
                    autoComplete="current-password"
                    className="pl-10 pr-10 h-11"
                    disabled={status === "loading"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrent(!showCurrent)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    tabIndex={-1}
                  >
                    {showCurrent ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* 새 비밀번호 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  새 비밀번호
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    type={showNew ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="8자 이상 입력"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    className="pl-10 pr-10 h-11"
                    disabled={status === "loading"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowNew(!showNew)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    tabIndex={-1}
                  >
                    {showNew ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  영문, 숫자를 포함하여 8자 이상
                </p>
              </div>

              {/* 새 비밀번호 확인 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  새 비밀번호 확인
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    type={showConfirm ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="새 비밀번호 다시 입력"
                    required
                    autoComplete="new-password"
                    className="pl-10 pr-10 h-11"
                    disabled={status === "loading"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    tabIndex={-1}
                  >
                    {showConfirm ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {/* 일치 여부 표시 */}
                {confirmPassword && (
                  <p
                    className={`mt-1 text-xs ${
                      newPassword === confirmPassword
                        ? "text-green-600"
                        : "text-red-500"
                    }`}
                  >
                    {newPassword === confirmPassword
                      ? "비밀번호가 일치합니다"
                      : "비밀번호가 일치하지 않습니다"}
                  </p>
                )}
              </div>

              {/* 제출 버튼 */}
              <Button
                type="submit"
                className="w-full h-11 mt-6"
                disabled={status === "loading"}
              >
                {status === "loading" ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    변경 중...
                  </>
                ) : (
                  "비밀번호 변경"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
