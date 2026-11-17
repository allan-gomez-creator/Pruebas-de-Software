# tareas/apps.py — CONFIGURACIÓN DE LA APP DE TAREAS (Sprint 3).
# Django lee esta clase cuando la app está en INSTALLED_APPS
# ('tareas.apps.TareasConfig' en Sprint_1/settings.py).

from django.apps import AppConfig


class TareasConfig(AppConfig):
    # Tipo de la columna "id" de las tablas de esta app: entero grande autoincremental.
    default_auto_field = 'django.db.models.BigAutoField'
    # Nombre del paquete de Python de la app (la carpeta "tareas").
    name = 'tareas'
    # Título con el que aparece la app en /admin/.
    verbose_name = 'Organizador de tareas y calendario'
