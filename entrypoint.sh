#!/usr/bin/env bash
set -euo pipefail

# Wait for DB: simple python loop (retries)
wait_for_db() {
  echo "Waiting for database..."
  python - <<'PY'
import os, time, sys
from django.db import connections
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE','hotel_booking.deployment'))
for _ in range(60):
    try:
        connections['default'].cursor()
        print("Database available")
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("Database did not become available", file=sys.stderr)
sys.exit(1)
PY
}

create_superuser_if_missing() {

  if [ -z "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
    echo "DJANGO_SUPERUSER_USERNAME not set — skipping superuser creation"
    return
  fi

  python - <<'PY'
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE','hotel_booking.deployment'))
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if not User.objects.filter(username=username).exists():
  if not password:
    print("ERROR: DJANGO_SUPERUSER_PASSWORD not set; cannot create superuser with password", file=sys.stderr)
    sys.exit(1)
  user = User.objects.create_superuser(username=username, email=email, password=password)
  # Set additional fields
  user.is_verified = True
  user.user_type ="admin"
  user.save()
  print(f"Superuser '{username}' created with email_verified and is_verified set to True.")
else:
  print(f"Superuser '{username}' already exists; skipping.")
PY
}

# 1) Wait for DB
wait_for_db

# 2) Apply migrations / collectstatic
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

# 3) Create superuser if missing
create_superuser_if_missing

# 4) Exec the CMD (start server)
exec "$@"
