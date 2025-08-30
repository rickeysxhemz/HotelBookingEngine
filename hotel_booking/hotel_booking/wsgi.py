"""
WSGI config for hotel_booking project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application



# Use DJANGO_SETTINGS_MODULE from environment if set, else default to development settings
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
	os.environ['DJANGO_SETTINGS_MODULE'] = 'hotel_booking.settings'

application = get_wsgi_application()
