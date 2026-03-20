#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! python -c "
import asyncio
import asyncpg
import os

async def check():
    try:
        url = os.environ.get('DATABASE_URL', '')
        conn = await asyncpg.connect(url)
        await conn.close()
        return True
    except:
        return False

exit(0 if asyncio.run(check()) else 1)
" 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is up!"

# Wait for Redis to be ready (optional)
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    REDIS_RETRIES=0
    REDIS_MAX_RETRIES=30
    while ! python -c "
import redis
import os

url = os.environ.get('REDIS_URL', '')
try:
    client = redis.from_url(url)
    client.ping()
    exit(0)
except:
    exit(1)
" 2>/dev/null; do
        REDIS_RETRIES=$((REDIS_RETRIES + 1))
        if [ $REDIS_RETRIES -ge $REDIS_MAX_RETRIES ]; then
            echo "Warning: Redis is unavailable after $REDIS_MAX_RETRIES retries - continuing without Redis"
            break
        fi
        echo "Redis is unavailable - sleeping (attempt $REDIS_RETRIES/$REDIS_MAX_RETRIES)"
        sleep 2
    done
    if [ $REDIS_RETRIES -lt $REDIS_MAX_RETRIES ]; then
        echo "Redis is up!"
    fi
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
