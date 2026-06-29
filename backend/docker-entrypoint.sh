#!/bin/sh
set -e

echo ">>> Applying database migrations..."
PYTHONPATH=/app alembic upgrade head
echo ">>> Migrations applied successfully."

echo ">>> Starting: $@"
exec "$@"
