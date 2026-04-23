#!/usr/bin/env bash
set -e

cd /app/hotel_booking

DB_HOST_VAL="${DB_HOST:-db}"
DB_PORT_VAL="${DB_PORT:-5432}"

# DB_USER, DB_PASSWORD, and DB_NAME must be supplied by the environment
# (e.g. Railway reference variables). No hardcoded defaults so that the
# real service credentials are never silently overridden.
if [ -z "${DB_USER}" ]; then
  echo "ERROR: DB_USER is not set. Set it to the Postgres username (e.g. via Railway reference variable DB_USER=\${{ Postgres.PGUSER }})." >&2
  exit 1
fi
if [ -z "${DB_PASSWORD}" ]; then
  echo "ERROR: DB_PASSWORD is not set. Set it to the Postgres password (e.g. via Railway reference variable DB_PASSWORD=\${{ Postgres.PGPASSWORD }})." >&2
  exit 1
fi
if [ -z "${DB_NAME}" ]; then
  echo "ERROR: DB_NAME is not set. Set it to the Postgres database name (e.g. via Railway reference variable DB_NAME=\${{ Postgres.PGDATABASE }})." >&2
  exit 1
fi

DB_USER_VAL="${DB_USER}"
DB_NAME_VAL="${DB_NAME}"

wait_for_db() {
  echo "Waiting for database at ${DB_HOST_VAL}:${DB_PORT_VAL}..."
  for i in {1..60}; do
    if pg_isready -h "$DB_HOST_VAL" -p "$DB_PORT_VAL" -U "$DB_USER_VAL" -d "$DB_NAME_VAL" 2>/dev/null; then
      echo "Database available"
      return 0
    fi
    sleep 1
  done
  echo "Database did not become ready in time — continuing anyway" >&2
}

create_superuser_if_missing() {
  if [ -z "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
    echo "Skipping superuser - DJANGO_SUPERUSER_USERNAME not set"
    return 0
  fi
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username=username, email=email, password=password)
    user.is_verified = True
    user.user_type = "admin"
    user.save()
    print(f"Superuser '{username}' created")
else:
    print(f"Superuser '{username}' already exists")
PY
}

# Skip heavy setup on non-web services (celery worker/beat should set RUN_SETUP=false).
if [ "${RUN_SETUP:-true}" = "true" ]; then
  wait_for_db
  echo "Running migrations..."
  python manage.py migrate --noinput
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
  echo "Setting up superuser..."
  create_superuser_if_missing
fi

# If a start command is provided (celery worker, beat, custom), exec it.
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

# Default: web service — bind to $PORT (Railway/Render) with 8000 fallback for local compose.
exec gunicorn hotel_booking.wsgi:application \
  --bind "0.0.0.0:${PORT:-${APP_PORT:-8000}}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout "${REQUEST_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
