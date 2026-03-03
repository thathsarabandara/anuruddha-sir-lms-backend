#!/bin/bash
# =============================================================================
# Docker entrypoint – runs one-time DB init/seed BEFORE gunicorn workers start.
# This prevents all 4 gunicorn workers from racing to initialise the database.
# =============================================================================

set -e

echo "============================================================"
echo " LMS Backend – Startup"
echo "============================================================"

# ---------------------------------------------------------------------------
# 1. One-time database initialisation + seeding.
#    SKIP_AUTO_INIT=false so create_app() runs init_database + auto_seed
#    exactly once here in the master process.
# ---------------------------------------------------------------------------
export SKIP_AUTO_INIT=false

echo "[entrypoint] Running one-time database init & seed..."
python -c "
from app import create_app
app = create_app()
print('[entrypoint] One-time init & seed complete.')
"

# ---------------------------------------------------------------------------
# 2. From here on every gunicorn worker imports main:app → create_app(),
#    but SKIP_AUTO_INIT=true means they skip init/seed entirely.
# ---------------------------------------------------------------------------
export SKIP_AUTO_INIT=true

echo "[entrypoint] Starting gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class gevent \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    main:app
