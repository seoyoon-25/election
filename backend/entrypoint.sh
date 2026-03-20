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

# Wait for Redis to be ready (optional) - simple timeout approach
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    sleep 5  # Give Redis time to start
    echo "Redis should be up (waited 5s)"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
