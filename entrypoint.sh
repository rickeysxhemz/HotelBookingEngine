#!/usr/bin/env bash
set -e

cd /app/hotel_booking

echo "=== env diagnostic ==="
echo "DATABASE_URL present: $([ -n "${DATABASE_URL:-}" ] && echo YES || echo NO)"
echo "DB_HOST: ${DB_HOST:-<unset>}"
echo "SECRET_KEY present: $([ -n "${SECRET_KEY:-}" ] && echo YES || echo NO)"
echo "ALLOWED_HOSTS: ${ALLOWED_HOSTS:-<unset>}"
echo "PORT: ${PORT:-<unset>}"
echo "====================="

# Prefer DATABASE_URL (Railway/Render), fall back to individual DB_* vars (compose).
if [ -n "${DATABASE_URL:-}" ]; then
  DB_HOST_VAL=$(python -c "from urllib.parse import urlparse; import os; print(urlparse(os.environ['DATABASE_URL']).hostname or '')")
  DB_PORT_VAL=$(python -c "from urllib.parse import urlparse; import os; print(urlparse(os.environ['DATABASE_URL']).port or 5432)")
  DB_USER_VAL=$(python -c "from urllib.parse import urlparse; import os; print(urlparse(os.environ['DATABASE_URL']).username or '')")
  DB_NAME_VAL=$(python -c "from urllib.parse import urlparse; import os; print((urlparse(os.environ['DATABASE_URL']).path or '').lstrip('/') or 'postgres')")
else
  DB_HOST_VAL="${DB_HOST:-db}"
  DB_PORT_VAL="${DB_PORT:-5432}"
  DB_USER_VAL="${DB_USER:-hotelapi_user}"
  DB_NAME_VAL="${DB_NAME:-hotelMaarDB}"
fi

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
