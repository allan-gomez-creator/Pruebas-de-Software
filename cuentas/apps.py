# CONFIGURACIÓN DE LA APP.
# Django lee esta clase cuando la app está en INSTALLED_APPS
# ('cuentas.apps.CuentasConfig' en settings.py).

from django.apps import AppConfig


class CuentasConfig(AppConfig):
    # Tipo de la columna "id" de las tablas de esta app: entero grande autoincremental.
    default_auto_field = 'django.db.models.BigAutoField'
    # Nombre del paquete de Python de la app (la carpeta "cuentas").
    name = 'cuentas'
    # Título con el que aparece la app en /admin/.
    verbose_name = 'Cuentas de usuario'
