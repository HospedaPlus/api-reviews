#!/bin/sh
set -e

# Migrations run before the API starts. Set RUN_MIGRATIONS=false for one-off
# containers (e.g. the seed task) or when migrations run as a separate ECS task.
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "==> Applying database migrations (alembic upgrade head)..."
    alembic upgrade head
fi

echo "==> Starting: $*"
exec "$@"
