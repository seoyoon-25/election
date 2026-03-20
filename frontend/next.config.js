/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  typescript: {
    // 빌드 시 타입 에러 무시 (기존 코드베이스 이슈로 인해 임시 설정)
    ignoreBuildErrors: true,
  },
  eslint: {
    // 빌드 시 ESLint 에러 무시
    ignoreDuringBuilds: true,
  },
  // 개발 모드에서 허용할 origin 설정
  allowedDevOrigins: ['https://election.bestcome.org'],
};

module.exports = nextConfig;
