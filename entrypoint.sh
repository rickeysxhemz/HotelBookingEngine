#!/usr/bin/env bash

cd /app/hotel_booking

wait_for_db() {
  echo "Waiting for database..."
  for i in {1..60}; do
    if pg_isready -h db -U hotelapi_user -d hotelMaarDB 2>/dev/null; then
      echo "Database available"
      break
    fi
    sleep 1
  done
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

# 1) Wait for DB
wait_for_db

# 2) Apply all migrations (CRITICAL - must succeed)
echo "Running migrations..."
python manage.py migrate

# 3) Collect static files (critical for WhiteNoise)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 4) Create superuser if missing
echo "Setting up superuser..."
create_superuser_if_missing

# 5) Start Gunicorn
exec gunicorn hotel_booking.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120

# 5) Start server (gunicorn handles static files via WhiteNoise middleware)
exec "$@"

