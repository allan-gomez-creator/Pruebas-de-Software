"""
MODELOS DE DATOS del módulo de tareas y calendario (Sprint 3).

Define únicamente la estructura de la tabla `tareas_tarea` en la base de datos.
"""

from django.conf import settings
from django.db import models


class EstadoTarea(models.TextChoices):
    """Estados permitidos para una tarea (CA-10)."""

    PENDIENTE = 'Pendiente', 'Pendiente'
    EN_PROGRESO = 'En progreso', 'En progreso'
    COMPLETADA = 'Completada', 'Completada'


class Tarea(models.Model):
    """Tabla `tareas_tarea` para el organizador de tareas y calendario (Sprint 3)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tareas',
        verbose_name='usuario',
    )
    nombre = models.CharField('nombre', max_length=150)
    descripcion = models.TextField('descripción', blank=True, default='')
    fecha_inicio = models.DateField('fecha de inicio')
    fecha_fin = models.DateField('fecha de fin')
    estado = models.CharField(
        'estado',
        max_length=20,
        choices=EstadoTarea.choices,
        default=EstadoTarea.PENDIENTE,
    )
    creado_en = models.DateTimeField('fecha de creación', auto_now_add=True)
    actualizado_en = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        db_table = 'tareas_tarea'
        verbose_name = 'tarea'
        verbose_name_plural = 'tareas'
        ordering = ['fecha_inicio', 'fecha_fin', 'nombre']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='tarea_fecha_fin_mayor_igual_inicio',
            ),
            models.CheckConstraint(
                condition=models.Q(
                    estado__in=[
                        EstadoTarea.PENDIENTE,
                        EstadoTarea.EN_PROGRESO,
                        EstadoTarea.COMPLETADA,
                    ]
                ),
                name='tarea_estado_valido',
            ),
        ]
