# student_site_vuln/settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-key-for-lab-only'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

ROOT_URLCONF = 'student_site_vuln.urls'

# settings.py (relevant parts)

INSTALLED_APPS = [
    'django.contrib.admin',          # nếu muốn dùng admin site
    'django.contrib.auth',           # bắt buộc cho user/auth/session
    'django.contrib.contenttypes',   # ⚠ bắt buộc, sửa lỗi ContentType
    'django.contrib.sessions',       # để dùng request.session
    'django.contrib.messages',       # nếu dùng messages
    'django.contrib.staticfiles',    # để dùng static
    'vulnapp',                       # app của bạn
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # --- session middleware phải nằm trước CommonMiddleware / CSRF ---
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # auth/messages middleware hữu ích (không bắt buộc nhưng nên có)
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'vulnapp' / 'templates'],  # hoặc nơi bạn lưu templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # cần để request trong template
                'django.contrib.auth.context_processors.auth', # ⚠ bắt buộc nếu dùng auth
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'student_site_vuln.wsgi.application'

# ---- Your SQL Server config (you already provided) ----
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'secureblogdb',
        'HOST': r'LIONKK\SEVER2024',
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'trusted_connection': 'yes',
        },
    },
}

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'vulnapp' / 'static']

import os

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')