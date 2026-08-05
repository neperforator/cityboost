#!/bin/sh
set -e

if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo ">>> Applying database migrations..."
    PYTHONPATH=/app alembic upgrade head
    echo ">>> Migrations applied successfully."
else
    echo ">>> Skipping database migrations (SKIP_MIGRATIONS=true)."
fi

echo ">>> Starting: $@"
exec "$@"
