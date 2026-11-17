
"""
Sprint_1/settings.py — CONFIGURACIÓN GENERAL del proyecto Django.

Configuración de aplicaciones, base de datos, autenticación,
seguridad, idioma, sesiones y correo electrónico.
"""

import os
from pathlib import Path

# Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# RECUPERACIÓN DE CONTRASEÑA (HU-03)
# =============================================================================

# Vigencia del enlace de recuperación: 30 minutos.
PASSWORD_RESET_TIMEOUT = 60 * 30


# =============================================================================
# SEGURIDAD
# =============================================================================

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-ujdih_llus32=mmvpf+hwpq0^#oe@n=ab*7#sscrw28^&1%pze',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1'
).split(',')


# =============================================================================
# APLICACIONES
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Aplicaciones del proyecto
    'despliegue',
    'cuentas.apps.CuentasConfig',
    'tareas.apps.TareasConfig',
]


# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # HU-04: evita almacenar en caché las páginas privadas.
    'cuentas.middleware.SinCachePrivadasMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================

ROOT_URLCONF = 'Sprint_1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Sprint_1.wsgi.application'


# =============================================================================
# BASE DE DATOS
# =============================================================================

DB_ENGINE = os.environ.get('DB_ENGINE', 'postgresql')

if DB_ENGINE == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': f'django.db.backends.{DB_ENGINE}',
            'NAME': os.environ.get('DB_NAME', 'postgres'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', '123456'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', ''),
        }
    }


# =============================================================================
# AUTENTICACIÓN (HU-01 / HU-02)
# =============================================================================

AUTH_USER_MODEL = 'cuentas.Usuario'

LOGIN_URL = 'cuentas:login'

LOGIN_REDIRECT_URL = 'cuentas:panel'

# =============================================================================
# CONTROL DE INTENTOS FALLIDOS DE AUTENTICACIÓN (HU-05)
# =============================================================================
# CA-05.1: máximo 5 intentos fallidos consecutivos para una misma combinación
#          de cuenta e IP durante una ventana de 15 minutos.
# CA-05.2: al superar el límite, bloqueo temporal durante 15 minutos.
AUTH_MAX_INTENTOS_FALLIDOS = int(os.environ.get('AUTH_MAX_INTENTOS_FALLIDOS', '5'))
AUTH_VENTANA_INTENTOS_MINUTOS = int(os.environ.get('AUTH_VENTANA_INTENTOS_MINUTOS', '15'))
AUTH_TIEMPO_BLOQUEO_MINUTOS = int(os.environ.get('AUTH_TIEMPO_BLOQUEO_MINUTOS', '15'))

# Algoritmo de hash de contraseñas (CA-01.7): PBKDF2-SHA256 con sal aleatoria
# y 1.500.000 iteraciones. Es el que Django usa por defecto; se deja escrito
# para que quede documentado. Nunca se guarda la contraseña en texto plano.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'cuentas.validators.ComplejidadContrasenaValidator',
    },
]


# =============================================================================
# IDIOMA Y ZONA HORARIA
# =============================================================================

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True
USE_TZ = True


# =============================================================================
# ARCHIVOS ESTÁTICOS
# =============================================================================

STATIC_URL = 'static/'


# =============================================================================
# CORREO ELECTRÓNICO (HU-03)
# =============================================================================

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

if EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_TIMEOUT = 20
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
else:
    EMAIL_BACKEND = 'cuentas.correo_consola.EmailBackend'
    DEFAULT_FROM_EMAIL = 'no-reply@tudominio.com'

ALTER USER postgres WITH PASSWORD '123456'
