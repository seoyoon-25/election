# 포트 요구사항

## 개발 환경 (docker-compose.yml)

| 서비스 | 내부 포트 | 외부 포트 | 설명 |
|--------|----------|----------|------|
| PostgreSQL | 5432 | 5433 | 로컬 PostgreSQL 충돌 방지 |
| Redis | 6379 | 6380 | 로컬 Redis 충돌 방지 |
| Backend (FastAPI) | 8000 | 8000 | API 서버 |
| Frontend (Next.js) | 3001 | 3001 | 웹 애플리케이션 |
| MinIO API | 9000 | 9000 | S3 호환 스토리지 |
| MinIO Console | 9001 | 9001 | MinIO 관리 UI |

## 운영 환경 (docker-compose.prod.yml)

| 서비스 | 내부 포트 | 외부 포트 | 설명 |
|--------|----------|----------|------|
| PostgreSQL | 5432 | - | 내부 네트워크 전용 |
| Redis | 6379 | - | 내부 네트워크 전용 |
| Backend (FastAPI) | 8000 | 8000 | Cloudflare 프록시 뒤에서 동작 |
| Frontend (Next.js) | 3000 | 3000 | Cloudflare 프록시 뒤에서 동작 |
| MinIO API | 9000 | - | 내부 네트워크 전용 |
| MinIO Console | 9001 | - | 내부 네트워크 전용 |

## 방화벽 설정

### 개발 환경
```bash
# 모든 포트 로컬 접근만 허용 (127.0.0.1)
```

### 운영 환경
```bash
# 필수 오픈 포트 (Cloudflare IP 범위만 허용 권장)
sudo ufw allow 80/tcp    # HTTP (Cloudflare 리디렉션)
sudo ufw allow 443/tcp   # HTTPS

# 내부 서비스 (외부 접근 차단)
# PostgreSQL(5432), Redis(6379), MinIO(9000/9001) - 컨테이너 내부 통신만
```

## 포트 충돌 해결

로컬에 PostgreSQL이나 Redis가 이미 실행 중인 경우:

```bash
# PostgreSQL 충돌 확인
lsof -i :5432

# Redis 충돌 확인
lsof -i :6379

# docker-compose.yml에서 호스트 포트 변경
# postgres: "5433:5432" → "5434:5432"
# redis: "6380:6379" → "6381:6379"
```

## 환경 변수

```env
# Backend
DATABASE_URL=postgresql://campaign_os:campaign_os@postgres:5432/campaign_os
REDIS_URL=redis://redis:6379/0

# Frontend
NEXT_PUBLIC_API_URL=https://election.bestcome.org/api/v1
```
