#!/bin/sh
# EduQuiz Bot — Docker backend entrypoint
#
# 1. Run Alembic migrations (idempotent — safe to run on every restart)
# 2. Start the application
#
# If migrations fail, the container exits immediately so Docker/compose
# can report the failure rather than starting with a broken schema.

set -e

echo "[entrypoint] Starting Database migrations..."
cd /app

if ! timeout 20s alembic upgrade head; then
    echo "❌ [entrypoint] FATAL ERROR: Alembic migrations failed or timed out!" >&2
    exit 1
fi
echo "✅ [entrypoint] Migrations complete."

echo "🚀 [entrypoint] Starting EduQuiz process..."
exec python -m app.main
