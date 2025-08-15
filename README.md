# Hotel Booking Engine

Django REST API for hotel booking management.

## Setup

```bash
pip install -r requirements.txt
cd hotel_booking
python manage.py migrate
python manage.py runserver
```

## Settings

- Development: `settings.py` (default)
- Production: `deployment.py` (set DJANGO_SETTINGS_MODULE=hotel_booking.deployment)

## API

- Auth: `/api/v1/auth/`
- Hotels: `/api/v1/hotels/`
- Bookings: `/api/v1/bookings/`
