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
    # Extract host and port from REDIS_URL (format: redis://host:port/db)
    REDIS_HOST=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]+):([0-9]+).*|\1|')
    REDIS_PORT=$(echo "$REDIS_URL" | sed -E 's|redis://([^:]+):([0-9]+).*|\2|')
    REDIS_RETRIES=0
    REDIS_MAX_RETRIES=30
    while ! timeout 2 bash -c "echo > /dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; do
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
