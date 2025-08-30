"""
ASGI config for hotel_booking project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application



# Use DJANGO_SETTINGS_MODULE from environment if set, else default to development settings
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
	os.environ['DJANGO_SETTINGS_MODULE'] = 'hotel_booking.settings'

application = get_asgi_application()
