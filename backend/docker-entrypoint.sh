#!/bin/sh
set -e

# Bind-mount ./storage перекрывает владельца из образа, поэтому при запуске
# от root выравниваем права и перезапускаем entrypoint от appuser.
if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/storage/uploads/tickets
    chown -R appuser:appgroup /app/storage
    exec gosu appuser "$0" "$@"
fi

if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo ">>> Applying database migrations..."
    PYTHONPATH=/app alembic upgrade head
    echo ">>> Migrations applied successfully."
else
    echo ">>> Skipping database migrations (SKIP_MIGRATIONS=true)."
fi

echo ">>> Starting: $@"
exec "$@"
