import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env (для локальной разработки)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-8x9k3m2p1n0b7v6c5x4z3a2s1d0f9g8h7j6k5l4m3n2b1v0c9x8z7a6s5d4f3')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    'mercury-restaurant.com',
    'www.mercury-restaurant.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'whitenoise.runserver_nostatic',
    'storages',                     # для облачного хранения
    'dashboard',
    'core',
    'menu',
    'orders',
    'bookings',
    'reviews',
    'users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mercury_project.urls'

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
                'core.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'mercury_project.wsgi.application'

# База данных
import dj_database_url

DATABASES = {
    'default': {}
}

if os.getenv('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
elif os.getenv('DB_NAME'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==================== НАСТРОЙКИ CLOUD.RU OBJECT STORAGE ====================
# ВНИМАНИЕ! Переменные окружения должны быть:
#   AWS_ACCESS_KEY_ID   = tenant_id:access_key (например, "97d67cc5-20f3-4b5a-81b9-15477565e497:a7d05ae4475004b0ecabd0d74ca1a7ce")
#   AWS_SECRET_ACCESS_KEY = ваш секретный ключ (6c0024e726ef4e73c94c37cc1050b15d)
#   AWS_STORAGE_BUCKET_NAME = mercury-media-ferczu
#   CLOUD_TENANT_ID (опционально, не используется в коде, оставлен для справки)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('CLOUD_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('CLOUD_BUCKET_NAME')
# TENANT_ID больше не нужен, так как он уже включён в AWS_ACCESS_KEY_ID
# AWS_S3_ENDPOINT_URL = f'https://s3.cloud.ru/{TENANT_ID}' – убираем, используем стандартный endpoint

# Эндпоинт для Cloud.ru (без tenant ID в пути, так как он уже в access key)
AWS_S3_ENDPOINT_URL = 'https://s3.cloud.ru'

# Настройки хранилищ (современный способ для Django 4.2+)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": "ru-msk-1",   # не используется, но требуется boto3
            "default_acl": "public-read",
            "querystring_auth": False,
            "signature_version": "s3v4",   # важно для Cloud.ru
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Базовый URL для медиа-файлов (используется в шаблонах)
# Он должен вести на публичный endpoint бакета
MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/media/'

# Дополнительные параметры для загружаемых файлов
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
    'ACL': 'public-read',
}

# Отключаем подписанные URL (для публичного доступа)
AWS_QUERYSTRING_AUTH = False
# ==================== КОНЕЦ НАСТРОЕК ОБЛАКА ====================

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'