"""
Production Django settings - Auto-configures from environment variables
Load this with: DJANGO_SETTINGS_MODULE=hotel_booking.production
"""

from .settings import *
import os

# ============================================================================
# ENVIRONMENT-BASED CONFIGURATION
# ============================================================================

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')

# Security - Read from environment with sensible defaults
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required!")

# Hosts configuration
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
for _default in ('.up.railway.app', '.railway.internal', 'localhost', '127.0.0.1'):
    if _default not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_default)
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME', 'hotelMaarDB'),
        'USER': os.environ.get('DB_USER', 'hotelapi_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', 600)),
        'ATOMIC_REQUESTS': os.environ.get('DB_ATOMIC_REQUESTS', 'False').lower() in ('true', '1'),
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# ============================================================================
# CACHE CONFIGURATION (Redis)
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': f'{ENVIRONMENT}_hotel',
        'TIMEOUT': int(os.environ.get('CACHE_TIMEOUT', 300)),
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = int(os.environ.get('SESSION_COOKIE_AGE', 1209600))

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@marhotels.com')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'noreply@marhotels.com')

# ============================================================================
# REDIS & CELERY CONFIGURATION
# ============================================================================

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_WORKER_PREFETCH_MULTIPLIER = int(os.environ.get('CELERY_WORKER_PREFETCH_MULTIPLIER', 1))
CELERY_WORKER_MAX_TASKS_PER_CHILD = int(os.environ.get('CELERY_WORKER_MAX_TASKS_PER_CHILD', 1000))

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# HTTPS/SSL Settings
USE_HTTPS = os.environ.get('USE_HTTPS', 'False').lower() in ('true', '1', 'yes')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS - HTTP Strict Transport Security
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() in ('true', '1', 'yes')
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'True').lower() in ('true', '1', 'yes')

# Cookie Security
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

# Content Security
SECURE_BROWSER_XSS_FILTER = os.environ.get('SECURE_BROWSER_XSS_FILTER', 'True').lower() in ('true', '1', 'yes')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ============================================================================
# CORS & DOMAINS CONFIGURATION
# ============================================================================

DOMAIN_NAME = os.environ.get('DOMAIN_NAME', 'localhost')
API_DOMAIN = os.environ.get('API_DOMAIN', DOMAIN_NAME)
FRONTEND_DOMAIN = os.environ.get('FRONTEND_DOMAIN', DOMAIN_NAME)

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOWED_ORIGINS = [o.strip() for o in CORS_ALLOWED_ORIGINS]
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
DJANGO_LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': LOG_LEVEL,
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
            'level': LOG_LEVEL,
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/security.log',
            'formatter': 'verbose',
            'level': 'WARNING',
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 10,
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/error.log',
            'formatter': 'verbose',
            'level': 'ERROR',
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 10,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'hotel_booking': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# ============================================================================
# RATE LIMITING
# ============================================================================

RATELIMIT_ENABLE = os.environ.get('RATELIMIT_ENABLE', 'True').lower() in ('true', '1', 'yes')
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = '100/h'

# ============================================================================
# STATIC & MEDIA FILES
# ============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = '/app/hotel_booking/staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# File upload constraints
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# ============================================================================
# MIDDLEWARE
# ============================================================================

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

# ============================================================================
# PRODUCTION-SPECIFIC OPTIMIZATIONS
# ============================================================================

# Disable default server-time header
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_SECURITY_POLICY = {
    'DEFAULT_SRC': ("'self'",),
    'SCRIPT_SRC': ("'self'", "'unsafe-inline'"),
    'STYLE_SRC': ("'self'", "'unsafe-inline'"),
    'IMG_SRC': ("'self'", "data:", "https:"),
}

# ============================================================================
# ADMIN CUSTOMIZATION
# ============================================================================

ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')

# ============================================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# ============================================================================

if ENVIRONMENT == 'development':
    DEBUG = True
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    
    # In development, allow localhost origins
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:8000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:8000',
    ]

elif ENVIRONMENT == 'staging':
    DEBUG = False
    # Staging uses dev-like security but production database
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False

elif ENVIRONMENT == 'production':
    DEBUG = False
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Production should have proper domains configured
