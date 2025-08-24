"""
WSGI config for hotel_booking project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


# DJANGO_SETTINGS_MODULE must be set in the environment for deployment.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_booking.settings')

application = get_wsgi_application()
