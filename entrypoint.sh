#!/usr/bin/env bash
set -e

cd /app/hotel_booking

wait_for_db() {
  echo "Waiting for database..."
  for i in {1..60}; do
    if python -c "import psycopg2,os; psycopg2.connect(host=os.environ.get('DB_HOST','db'),port=os.environ.get('DB_PORT','5432'),user=os.environ.get('DB_USER','hotelapi_user'),password=os.environ.get('DB_PASSWORD',''),dbname=os.environ.get('DB_NAME','hotelMaarDB')).close()" 2>/dev/null; then
      echo "Database available"
      return 0
    fi
    sleep 1
  done
  echo "Database did not become available in time" >&2
  return 1
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

# Skip setup on celery worker / beat services so only the web service migrates.
if [ "${RUN_SETUP:-true}" = "true" ]; then
  wait_for_db
  echo "Running migrations..."
  python manage.py migrate --noinput
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
  echo "Setting up superuser..."
  create_superuser_if_missing
fi

# If a command is provided (e.g. celery, custom gunicorn), run it.
# Otherwise start gunicorn on $PORT (Railway/Render) or 8000 (compose).
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn hotel_booking.wsgi:application \
  --bind "0.0.0.0:${PORT:-${APP_PORT:-8000}}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout "${REQUEST_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
