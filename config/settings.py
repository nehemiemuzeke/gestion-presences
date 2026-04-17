"""
Django Settings - Gestion des Présences
Configuration pour développement ET production
"""

from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url
import os

# ─────────────────────────────────────────
# CHEMINS DE BASE
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────
# SÉCURITÉ
# ─────────────────────────────────────────
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-change-me-in-production-xyz-123'
)
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1'
).split(',')

# Pour Railway (accepte tous les hosts en production)
ALLOWED_HOSTS += ['*.railway.app', '*']


# ─────────────────────────────────────────
# APPLICATIONS INSTALLÉES
# ─────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
]

LOCAL_APPS = [
    'accounts',
    'academic',
    'attendance',
    'dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ─────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ─────────────────────────────────────────
# URLS ET WSGI
# ─────────────────────────────────────────
ROOT_URLCONF    = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND' : 'django.template.backends.django.DjangoTemplates',
        'DIRS'    : [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS' : {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ─────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Production → PostgreSQL sur Railway
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # Développement → SQLite local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME'  : BASE_DIR / 'db.sqlite3',
        }
    }


# ─────────────────────────────────────────
# MODÈLE UTILISATEUR PERSONNALISÉ
# ─────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'


# ─────────────────────────────────────────
# VALIDATION DES MOTS DE PASSE
# ─────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.UserAttributeSimilarityValidator',
    },
    {
        'NAME'   : 'django.contrib.auth.password_validation'
                   '.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.NumericPasswordValidator',
    },
]


# ─────────────────────────────────────────
# DJANGO REST FRAMEWORK
# ─────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE'       : 20,
    'DATETIME_FORMAT' : '%Y-%m-%d %H:%M:%S',
}


# ─────────────────────────────────────────
# JWT
# ─────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS' : True,
    'ALGORITHM'             : 'HS256',
    'SIGNING_KEY'           : SECRET_KEY,
    'AUTH_HEADER_TYPES'     : ('Bearer',),
}


# ─────────────────────────────────────────
# CORS
# ─────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS  = True
CORS_ALLOW_ALL_ORIGINS  = True  # Pour Railway


# ─────────────────────────────────────────
# INTERNATIONALISATION
# ─────────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Abidjan'
USE_I18N      = True
USE_TZ        = True


# ─────────────────────────────────────────
# FICHIERS STATIQUES ET MÉDIAS
# ─────────────────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ─────────────────────────────────────────
# SÉCURITÉ PRODUCTION
# ─────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER     = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT         = True
    SESSION_COOKIE_SECURE       = True
    CSRF_COOKIE_SECURE          = True
    SECURE_BROWSER_XSS_FILTER   = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS             = 'DENY'


# ─────────────────────────────────────────
# DIVERS
# ─────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL           = '/auth/login/'
LOGIN_REDIRECT_URL  = '/dashboard/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# ─────────────────────────────────────────
# PARAMÈTRES MÉTIER
# ─────────────────────────────────────────
GPS_RADIUS_METERS       = int(config('GPS_RADIUS_METERS', default=15))
ATTENDANCE_CODE_DURATION = int(config('ATTENDANCE_CODE_DURATION', default=10))
ABSENCE_THRESHOLD       = int(config('ABSENCE_THRESHOLD', default=3))
LATE_THRESHOLD_MINUTES  = int(config('LATE_THRESHOLD_MINUTES', default=15))

# ─────────────────────────────────────────
# MESSAGES
# ─────────────────────────────────────────
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG  : 'debug',
    messages.INFO   : 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR  : 'danger',
}

# ─────────────────────────────────────────
# PAGES D'ERREUR
# ─────────────────────────────────────────
handler404 = 'config.views.page_404'
handler500 = 'config.views.page_500'