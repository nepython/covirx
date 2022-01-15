"""
Django settings for CoviRx project.

Generated by 'django-admin startproject' using Django 3.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-nyjf++o-0m8d&!q3qln!8yj3@cvgx$1iqz)1)0**_uqps%sxlq'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', True)
if type(DEBUG)==str: # since environment variable would be a string
    if DEBUG.lower()=='false':
        DEBUG=False
    else:
        DEBUG=True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'main',  # the name of our app
    'flat_json_widget', # Used to display custom_fields nicely
    'admin_interface', # Used to customize django admin
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
]

AUTH_USER_MODEL = 'accounts.User'

X_FRAME_OPTIONS='SAMEORIGIN'
SILENCED_SYSTEM_CHECKS = ['security.W019']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'CoviRx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.last_update_processor'
            ],
        },
    },
]

WSGI_APPLICATION = 'CoviRx.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
            'check_same_thread': False,
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = 'home'


EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

if not EMAIL_HOST_USER:
    logging.getLogger('error_logger').error('\033[22;33mYou have not specified the variable "EMAIL_HOST_USER" in your .env file. Email functionality will not work.\033[0;0m')
if not EMAIL_HOST_PASSWORD:
    logging.getLogger('error_logger').error('\033[22;33mYou have not specified the variable "EMAIL_HOST_PASSWORD" in your .env file. Email functionality will not work.\033[0;0m')


# For OAuth2
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
# For ReCaptcha
GOOGLE_INVISIBLE_RECAPTCHA_SECRET_KEY = os.getenv('GOOGLE_INVISIBLE_RECAPTCHA_SECRET_KEY')

# PRODUCTION SETTINGS
if not DEBUG:
    import django_heroku
    django_heroku.settings(locals())
    MIDDLEWARE += ('whitenoise.middleware.WhiteNoiseMiddleware',) # django-heroku changes type from list to tuple
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    ALLOWED_HOSTS += ['covirx.herokuapp.com']
    SECRET_KEY = os.getenv('SECRET_KEY')
