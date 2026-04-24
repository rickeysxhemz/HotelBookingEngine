# Authentication backends: use custom email backend and Django's default
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
import os
from pathlib import Path
from datetime import timedelta
from django.contrib.messages import constants as messages
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Remove fallback for production security - SECRET_KEY must be set in environment
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

def _parse_allowed_hosts(raw):
    hosts = [h.strip() for h in (raw or '').split(',') if h.strip()]
    # Always include Railway's edge + internal networking so healthchecks pass.
    for default in ('.up.railway.app', '.railway.internal', 'localhost', '127.0.0.1'):
        if default not in hosts:
            hosts.append(default)
    return hosts or ['*']

ALLOWED_HOSTS = _parse_allowed_hosts(config('ALLOWED_HOSTS', default=''))

# Application definition
INSTALLED_APPS = [
    'jazzmin',  
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
     # Third-party apps
    'drf_spectacular',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'accounts',
    'bookings',
    'core',
    'manager',
    'offers',
    'payments',  # Tap Payments integration app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hotel_booking.urls'
WSGI_APPLICATION = 'hotel_booking.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
    from urllib.parse import urlparse
    _parsed = urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _parsed.path.lstrip('/') or 'postgres',
            'USER': _parsed.username or '',
            'PASSWORD': _parsed.password or '',
            'HOST': _parsed.hostname or '',
            'PORT': _parsed.port or 5432,
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='hotelMaarDB'),
            'USER': config('DB_USER', default='hotelapi_user'),
            'PASSWORD': config('DB_PASSWORD', default='hotelapi_secure_password'),
            'HOST': config('DB_HOST', default='db'),
            'PORT': config('DB_PORT', default='5432', cast=int),
            'CONN_MAX_AGE': 600,
        }
    }

# Redis and Caching configuration for production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'hotel_booking',
        'TIMEOUT': 300,
    }
}

# Celery Configuration for Async Tasks
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/1')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Celery Beat Schedule Configuration
CELERY_BEAT_SCHEDULE = {
    'check-booking-expiry': {
        'task': 'bookings.tasks.check_pending_booking_expiry',
        'schedule': 30 * 60,  # Every 30 minutes
    },
    'send-reminder-emails': {
        'task': 'bookings.tasks.send_check_in_reminders',
        'schedule': 3600,  # Every 1 hour
    },
    'cleanup-cancelled-bookings': {
        'task': 'bookings.tasks.cleanup_cancelled_bookings',
        'schedule': 86400,  # Daily
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Security Settings
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session Security
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Set session cookie age to 1 hour (3600 seconds)

SESSION_COOKIE_AGE = 2 * 24 * 60 * 60

# Enable these in production with HTTPS
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Used in production
 
# In development, add app static dirs for static file serving
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'hotel_booking' / 'manager' / 'static']
MEDIA_URL = '/media/'
# Set media root to match Docker volume mounting
MEDIA_ROOT = Path('/app/media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'


# Email Configuration
if DEBUG:
    # In development, use console backend to print emails to console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # In production, use Gmail SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Hotel Booking <noreply@example.com>')
SERVER_EMAIL = config('SERVER_EMAIL', default='Hotel Booking <noreply@example.com>')

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# CORS configuration - MUST be overridden in production deployment.py
# Development defaults only - DO NOT use in production
_DEFAULT_CORS = (
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:8080,"
    "http://127.0.0.1:8080"
)
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default=_DEFAULT_CORS,
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
)

# WARNING: This is for development only
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# DRF Spectacular Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Hotel Booking Engine API',
    'DESCRIPTION': 'Hotel booking and management API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_COERCE_PATH_PK_TO_STRING': False,
    'SCHEMA_COERCE_METHOD_NAMES': {
        'retrieve': 'get',
        'destroy': 'delete',
    },
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'displayRequestDuration': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'docExpansion': 'list',
        'filter': True,
        'syntaxHighlight.activate': True,
        'syntaxHighlight.theme': 'agate',
        'tryItOutEnabled': True,
        'requestSnippetsEnabled': True,
        'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
        'validatorUrl': None,
        'withCredentials': True,
        'showMutatedRequest': True,
        'defaultModelRendering': 'example',
        'defaultModelExpandDepth': 2,
        'defaultModelsExpandDepth': 1,
        'displayRequestDuration': True,
        'showExtensions': True,
        'showCommonExtensions': True,
    },
    'SWAGGER_UI_FAVICON_HREF': '/static/favicon.ico',
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'expandResponses': '200,201',
        'expandSingleSchemaField': True,
        'hideHostname': False,
        'hideLoading': False,
        'nativeScrollbars': False,
        'pathInMiddlePanel': False,
        'requiredPropsFirst': True,
        'scrollYOffset': 0,
        'sortPropsAlphabetically': False,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#32329f'
                }
            }
        }
    },
    # Schema generation settings
    'SORT_OPERATIONS': True,
    'ENABLE_DJANGO_DEPLOY_CHECK': True,
    'DISABLE_ERRORS_AND_WARNINGS': False,
    'ENUM_NAME_OVERRIDES': {},
    'ENUM_GENERATE_CHOICE_DESCRIPTION': True,
    'POSTPROCESSING_HOOKS': [
        'core.spectacular_hooks.postprocess_enhanced_schema'
    ],
    # Component naming
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    # Field handling
    'DISABLE_ERRORS_AND_WARNINGS': False,
    'SCHEMA_COERCE_PATH_PK': True,
    'GENERIC_ADDITIONAL_PROPERTIES': 'dict',
    # Authentication
    'SERVE_AUTHENTICATION': None,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_PUBLIC': True,
}

TAP_SECRET_KEY = config('TAP_SECRET_KEY', default='')
TAP_API_KEY = config('TAP_API_KEY', default='')
TAP_MERCHANT_ID = config('TAP_MERCHANT_ID', default='')
TAP_WEBHOOK_SECRET = config('TAP_WEBHOOK_SECRET', default='')

SITE_URL = config('SITE_URL', default='http://localhost:5173')

