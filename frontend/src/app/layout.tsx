import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: "캠프보드 - 선거캠프 업무 관리",
  description: "선거캠프 실무를 한곳에서 관리하는 업무 공간",
  keywords: ["선거", "캠프", "업무관리", "태스크", "협업"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
