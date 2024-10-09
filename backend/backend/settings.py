"""
Django settings for transcendence project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from datetime import timedelta
import toml

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    # Formatters define the structure of the log messages
    'formatters': {
        'verbose': {
            'format': '[{asctime}] [{levelname}] [{module}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },

    # Handlers define how the logs will be processed (e.g., console or file)
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
    },

    # Loggers define the actual log groups for your project
    'loggers': {
        'django': {  # Logger for Django core components
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'daphne': {  # Logger for Daphne
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'match': {  # Logger for handling match-specific logs
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'tournament': {  # Logger for handling tournament-specific logs
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'matchmaking_consumer': {  # Logger for handling MatchmakingConsumer-specific logs
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'match_consumer': {  # Logger for handling MatchConsumer-specific logs
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'game_session': {  # Logger for handling GameSession-specific logs
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'data_managment': {  # Logger for handling Datamanagment-specific logs (e.g., Matches, Users, etc.)
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Path to the configuration files
PONG_CONFIG_FILE_PATH = os.path.join(BASE_DIR, 'pong', 'config.toml')

# Read the configuration file
with open(PONG_CONFIG_FILE_PATH, 'r') as config_file:
     config = toml.load(config_file)

GAME_CONFIG = config['game']
MATCH_CONFIG = config['match']
TOURNAMENT_CONFIG = config['tournament']
     

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-g=eom8w39!m$+1xegc@p!(6&uiqzdl$9i@$v5z!f$@m#2#_!7s'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True

# #TODO:  SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

#TODO: change to specific hosts
ALLOWED_HOSTS = ["10.12.8.1", "localhost", "127.0.0.1"]

BASE_IP = "10.12.8.1"

# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
    'usermanagement',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'pong',
]

ASGI_APPLICATION = "backend.asgi.application"

REDIS_HOST = 'redis' # Redis server address
REDIS_PORT = 6379    # or your Redis server port

# Redis cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'backend.middleware.AuthorizationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# Only for development!!! Disable template caching # TODO: Remove this in production
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': False,  # Changed to False
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

# Original TEMPLATES setting
# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# can this be defined somewhere else as it is also in usermanagement/utils.py
def get_secret(secret_name):
    try:
        with open(f'/run/secrets/{secret_name}') as secret_file:
            return secret_file.read().strip()
    except IOError as e:
            raise Exception(f'Critical error reading secret {secret_name}: {e}')


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_secret('psql_database'),
        'USER': get_secret('psql_user'),
        'PASSWORD': get_secret('psql_password'),
        'HOST': 'postgresql',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# For development only # To show the admin page correctly # TODO: Remove this in production

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "/mediafiles/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")

CSRF_TRUSTED_ORIGINS = [
     'https://localhost',
     'http://localhost',
     'http://127.0.0.1',
     'https://127.0.0.1'
]

# Original STATIC_URL setting
# STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#TODO: change to specific cors
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWS_CREDENTIALS = True


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        #"rest_framework_simplejwt.authentication.JWTAuthentication",
        'rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication',
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    "AUTH_COOKIE": 'access_token',
    "AUTH_COOKIE_REFRESH": 'refresh_token',
    "AUTH_COOKIE_DOMAIN": None,
    "AUTH_COOKIE_SECURE": True,
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_PATH": '/',
    "AUTH_COOKIE_REFRESH_PATH": '/api/token/',
    "AUTH_COOKIE_SAMESITE": 'Strict',
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=5),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    #add additional settings, e.g. algo?
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'Transcendence Pongo API',
    'DESCRIPTION': 'API for the Transcendence Pongo project',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}


AUTH_USER_MODEL = 'usermanagement.CustomUser'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = get_secret('email_host')
EMAIL_HOST_PASSWORD = get_secret('email_pw')

