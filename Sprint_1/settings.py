"""
Sprint_1/settings.py — CONFIGURACIÓN GENERAL del proyecto Django.

Django lee este archivo al arrancar. Aquí se define qué apps usa el
proyecto, a qué base de datos se conecta, el idioma, las reglas de
contraseña y cómo funciona el inicio de sesión.

Generado por 'django-admin startproject' (Django 6.1.2) y modificado para
HU-01 (registro), HU-02 (inicio de sesión) y HU-05 (límite de intentos fallidos).
Documentación: https://docs.djangoproject.com/en/6.1/ref/settings/
"""

import os                      # para leer variables de entorno (os.environ)
from pathlib import Path       # para armar rutas de carpetas sin importar el sistema operativo

# Carpeta raíz del proyecto (la que contiene manage.py).
# __file__ es este archivo; .parent.parent sube dos niveles: Sprint_1/ -> raíz.
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# SEGURIDAD
# =============================================================================

# Clave secreta: Django la usa para firmar cookies de sesión y tokens CSRF.
# os.environ.get('X', 'valor') lee la variable de entorno X; si no existe,
# usa 'valor'. En desarrollo se usa la clave de abajo; en un servidor real
# se define la variable DJANGO_SECRET_KEY y nunca se sube al repositorio.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-ujdih_llus32=mmvpf+hwpq0^#oe@n=ab*7#sscrw28^&1%pze',
)

# DEBUG=True muestra páginas de error detalladas. Solo para desarrollo.
# Se apaga definiendo la variable de entorno DJANGO_DEBUG=False.
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# Dominios desde los que se puede abrir el sitio. split(',') convierte
# 'localhost,127.0.0.1' en la lista ['localhost', '127.0.0.1'].
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# =============================================================================
# APLICACIONES
# =============================================================================
# Django solo usa las apps que están en esta lista.

INSTALLED_APPS = [
    # Apps que trae Django
    'django.contrib.admin',          # panel /admin/
    'django.contrib.auth',           # usuarios, contraseñas, login
    'django.contrib.contenttypes',   # lo necesitan auth y admin
    'django.contrib.sessions',       # sesiones (mantener al usuario conectado)
    'django.contrib.messages',       # mensajes de una sola vez ("¡Cuenta creada!")
    'django.contrib.staticfiles',    # archivos CSS y JavaScript
    # Apps del proyecto
    'despliegue',                    # la app del "Hola Mundo" original
    'cuentas.apps.CuentasConfig',    # HU-01 Registro, HU-02 Inicio de sesión y HU-05 Control de intentos
]

# Middleware: capas por las que pasa CADA petición antes de llegar a la vista
# (y cada respuesta al salir). El orden importa; se deja el de Django.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',            # cabeceras de seguridad
    'django.contrib.sessions.middleware.SessionMiddleware',     # carga la sesión desde la cookie
    'django.middleware.common.CommonMiddleware',                # ajustes comunes de URLs
    'django.middleware.csrf.CsrfViewMiddleware',                # exige token CSRF en los POST
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # pone request.user (usuario actual)
    'django.contrib.messages.middleware.MessageMiddleware',     # habilita messages.success(...)
    'django.middleware.clickjacking.XFrameOptionsMiddleware',   # evita que el sitio se meta en un iframe ajeno
]

# Archivo con las rutas principales del proyecto.
ROOT_URLCONF = 'Sprint_1.urls'

# Plantillas HTML.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        # APP_DIRS=True: Django busca plantillas en la carpeta templates/ de
        # cada app (por eso encuentra cuentas/templates/cuentas/login.html).
        'APP_DIRS': True,
        'OPTIONS': {
            # Variables disponibles en TODAS las plantillas sin pasarlas a mano:
            'context_processors': [
                'django.template.context_processors.request',            # {{ request }}
                'django.contrib.auth.context_processors.auth',           # {{ user }}
                'django.contrib.messages.context_processors.messages',   # {{ messages }}
            ],
        },
    },
]

WSGI_APPLICATION = 'Sprint_1.wsgi.application'


# =============================================================================
# BASE DE DATOS (Integración rama master PostgreSQL + entorno de pruebas)
# =============================================================================
# Por defecto SQLite (un archivo db.sqlite3; no hay que instalar nada).
# Para usar PostgreSQL (base de datos 'pruebas' definida en la rama master)
# basta con definir DB_ENGINE=postgresql en las variables de entorno:
#   DB_ENGINE=postgresql DB_NAME=pruebas DB_USER=postgres DB_PASSWORD=Juan1014
# `python manage.py test` crea sola una BD independiente test_<DB_NAME> y la
# borra al terminar (requisito del plan de pruebas, sección 3.2).

DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite3')

if DB_ENGINE == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',     # archivo en la raíz del proyecto
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': f'django.db.backends.{DB_ENGINE}',            # postgresql | mysql
            'NAME': os.environ.get('DB_NAME', 'pruebas'),           # nombre de la BD en rama master
            'USER': os.environ.get('DB_USER', 'postgres'),          # usuario del motor en rama master
            'PASSWORD': os.environ.get('DB_PASSWORD', 'Juan1014'),  # contraseña configurable
            'HOST': os.environ.get('DB_HOST', 'localhost'),         # servidor
            'PORT': os.environ.get('DB_PORT', ''),                  # puerto (vacío = el del motor)
        }
    }


# =============================================================================
# AUTENTICACIÓN (HU-01 / HU-02 / HU-05)
# =============================================================================

# Usar NUESTRO modelo de usuario (formato 'app.Modelo') en lugar del User de
# Django. Debe definirse ANTES de la primera migración.
AUTH_USER_MODEL = 'cuentas.Usuario'

# Nombre de la ruta a la que @login_required manda a quien no tiene sesión (CA-02.6).
LOGIN_URL = 'cuentas:login'

# Ruta por defecto después de iniciar sesión (CA-02.5).
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

# Reglas de contraseña: EXACTAMENTE las de CA-01.4. Se quitan dos validadores
# que Django trae por defecto porque agregan reglas que el Product Owner no pidió:
#   - CommonPasswordValidator rechaza "Abcd1234" (está en su lista de
#     contraseñas comunes) y el caso CP-06 espera que sea ACEPTADA.
#   - UserAttributeSimilarityValidator rechaza contraseñas parecidas al correo.
# Django ejecuta esta lista en orden cada vez que se llama a validate_password().
AUTH_PASSWORD_VALIDATORS = [
    {
        # Regla 1: mínimo 8 caracteres (validador incluido en Django).
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        # Reglas 2 a 4: mayúscula, minúscula y número (cuentas/validators.py).
        'NAME': 'cuentas.validators.ComplejidadContrasenaValidator',
    },
]


# =============================================================================
# IDIOMA Y ZONA HORARIA
# =============================================================================

# Español de Colombia: traduce los mensajes propios de Django
# (admin, "La contraseña es demasiado corta...").
LANGUAGE_CODE = 'es-co'

# Zona horaria de Colombia (UTC-5) para mostrar fechas y horas.
TIME_ZONE = 'America/Bogota'

USE_I18N = True     # activar traducciones
USE_TZ = True       # guardar fechas en UTC y convertirlas a TIME_ZONE al mostrarlas


# =============================================================================
# ARCHIVOS ESTÁTICOS (CSS, JavaScript, imágenes)
# =============================================================================
# URL desde la que se sirven. Ej.: /static/cuentas/css/estilos.css
STATIC_URL = 'static/'


# =============================================================================
# CORREO
# =============================================================================
# Backend de consola: en lugar de enviar correos, los imprime en la terminal
# donde corre el servidor. Sirve como "buzón de desarrollo" para HU-03
# (recuperar contraseña), que es de otro compañero.
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
