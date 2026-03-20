# 백업 절차 가이드

## 개요
CampBoard 시스템의 데이터 백업 및 복구 절차를 정의합니다.

---

## 백업 대상

| 구분 | 데이터 | 백업 주기 |
|------|--------|----------|
| PostgreSQL | 사용자, 캠페인, 작업, 결재 등 | 매일 |
| Redis | 세션, 토큰 블랙리스트 | 선택적 |
| MinIO | 업로드된 파일 | 매일 |
| 설정 파일 | .env, docker-compose.yml | 변경 시 |

---

## PostgreSQL 백업

### 자동 백업 스크립트

```bash
#!/bin/bash
# /var/www/election/scripts/backup-db.sh

BACKUP_DIR="/var/backups/election"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="election"
RETENTION_DAYS=7

mkdir -p $BACKUP_DIR

# Docker 컨테이너에서 pg_dump 실행
docker exec election-postgres pg_dump -U postgres $DB_NAME | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# 오래된 백업 삭제
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_DIR/db_$TIMESTAMP.sql.gz"
```

### 수동 백업

```bash
# 전체 데이터베이스 백업
docker exec election-postgres pg_dump -U postgres election > backup.sql

# 특정 테이블만 백업
docker exec election-postgres pg_dump -U postgres -t users -t campaigns election > partial_backup.sql
```

### 복구

```bash
# 전체 복구
cat backup.sql | docker exec -i election-postgres psql -U postgres election

# 새 데이터베이스에 복구
docker exec election-postgres psql -U postgres -c "CREATE DATABASE election_restored"
cat backup.sql | docker exec -i election-postgres psql -U postgres election_restored
```

---

## MinIO (파일 스토리지) 백업

### mc 클라이언트 설정

```bash
# MinIO 클라이언트 설치
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# 서버 등록
mc alias set election http://localhost:9000 minioadmin minioadmin
```

### 백업

```bash
# 전체 버킷 백업
mc mirror election/election-files /var/backups/election/files/

# 특정 경로만 백업
mc cp --recursive election/election-files/avatars /var/backups/election/avatars/
```

### 복구

```bash
mc mirror /var/backups/election/files/ election/election-files
```

---

## Redis 백업 (선택적)

Redis는 주로 캐시 용도로 사용되므로 필수 백업 대상이 아닙니다.
세션 데이터가 중요한 경우에만 백업합니다.

```bash
# RDB 스냅샷 생성
docker exec election-redis redis-cli BGSAVE

# 스냅샷 파일 복사
docker cp election-redis:/data/dump.rdb /var/backups/election/redis_dump.rdb
```

---

## Cron 스케줄 설정

```bash
# crontab -e
# 매일 새벽 3시 데이터베이스 백업
0 3 * * * /var/www/election/scripts/backup-db.sh >> /var/log/election-backup.log 2>&1

# 매일 새벽 4시 파일 스토리지 백업
0 4 * * * mc mirror election/election-files /var/backups/election/files/ >> /var/log/election-backup.log 2>&1
```

---

## 백업 검증

주기적으로 백업 복구 테스트를 수행하여 백업의 유효성을 확인합니다.

### 검증 절차

1. 테스트 환경에서 백업 복구 실행
2. 데이터 무결성 확인 (레코드 수, 핵심 데이터 검증)
3. 애플리케이션 기능 테스트

```bash
# 백업 파일 무결성 검사
gunzip -t /var/backups/election/db_*.sql.gz

# 레코드 수 확인 (복구 후)
docker exec election-postgres psql -U postgres election -c "SELECT COUNT(*) FROM users"
```

---

## 재해 복구 시나리오

### 데이터베이스 손상 시

1. 서비스 중단 알림
2. 최신 백업 파일 확인
3. 새 데이터베이스 인스턴스 생성
4. 백업 복구
5. 데이터 검증
6. 서비스 재개

### 서버 전체 장애 시

1. 새 서버 프로비저닝
2. Docker 환경 설정
3. 백업 파일 복원 (DB + Files)
4. 환경 변수 설정
5. 서비스 시작 및 검증

---

## 연락처

- 긴급 상황: 시스템 관리자에게 연락
- 백업 이슈: ops@example.com

---

*마지막 업데이트: 2026-03-20*
