"""
cuentas/services.py — SERVICIO DE CONTROL DE INTENTOS FALLIDOS (HU-05).

Diseño orientado a los principios SOLID:
  - S (Single Responsibility Principle): `LimitadorIntentosService` tiene una
    única responsabilidad: aplicar la política de límite de intentos fallidos
    y bloqueo temporal por combinación de cuenta e IP (CA-05.1 a CA-05.5),
    desacoplándola del formulario HTTP (`forms.py`) y de las vistas (`views.py`).
  - O (Open/Closed Principle): los umbrales (máximo de intentos, duración de la
    ventana y duración del bloqueo) se leen desde `settings.py`, permitiendo
    ajustar la política sin modificar el código del servicio.
  - D (Dependency Inversion Principle): los formularios dependen de la interfaz
    de alto nivel de este servicio y de las abstracciones de Django ORM / Timezone.
"""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from .models import IntentoAcceso, normalizar_email


class LimitadorIntentosService:
    """Gestiona el conteo de intentos fallidos y el bloqueo temporal (HU-05)."""

    @staticmethod
    def max_intentos() -> int:
        """CA-05.1: máximo de intentos fallidos consecutivos permitidos (por defecto 5)."""
        return getattr(settings, 'AUTH_MAX_INTENTOS_FALLIDOS', 5)

    @staticmethod
    def ventana_minutos() -> int:
        """CA-05.1: ventana de tiempo en minutos para acumular intentos (por defecto 15)."""
        return getattr(settings, 'AUTH_VENTANA_INTENTOS_MINUTOS', 15)

    @staticmethod
    def tiempo_bloqueo_minutos() -> int:
        """CA-05.2: duración del bloqueo temporal en minutos (por defecto 15)."""
        return getattr(settings, 'AUTH_TIEMPO_BLOQUEO_MINUTOS', 15)

    @staticmethod
    def obtener_ip_cliente(request: HttpRequest | None) -> str:
        """Obtiene la dirección IP del cliente a partir de la petición HTTP."""
        if request is None:
            return '127.0.0.1'
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip() or '127.0.0.1'
        return (request.META.get('REMOTE_ADDR') or '127.0.0.1').strip()

    @classmethod
    def obtener_registro(cls, email: str, ip_address: str) -> IntentoAcceso | None:
        """Busca el registro de intentos para la combinación (cuenta, IP)."""
        email_norm = normalizar_email(email)
        ip_norm = (ip_address or '127.0.0.1').strip()
        return IntentoAcceso.objects.filter(
            email__iexact=email_norm,
            ip_address=ip_norm,
        ).first()

    @classmethod
    def esta_bloqueado(cls, email: str, ip_address: str, ahora=None) -> bool:
        """Verifica si la combinación (cuenta, IP) está bloqueada actualmente.

        - CA-05.2: Si superó el límite y no han pasado 15 minutos, devuelve True.
        - CA-05.4: Si el período de bloqueo de 15 minutos ya concluyó (o la
          ventana de 15 minutos expiró), reinicia el estado automáticamente y
          devuelve False para permitir un nuevo intento de inicio de sesión.
        """
        momento = ahora or timezone.now()
        registro = cls.obtener_registro(email, ip_address)
        if registro is None:
            return False

        # Si tenía un bloqueo registrado:
        if registro.bloqueado_hasta is not None:
            if registro.esta_bloqueado(ahora=momento):
                return True
            # CA-05.4: El bloqueo ya expiró -> se limpia el contador para permitir reintentar.
            registro.intentos_fallidos = 0
            registro.bloqueado_hasta = None
            registro.primer_intento_en = momento
            registro.ultimo_intento_en = momento
            registro.save()
            return False

        # Si no estaba bloqueado pero la ventana de 15 minutos ya expiró (CA-05.1):
        if registro.intentos_fallidos > 0 and registro.ventana_expirada(
            cls.ventana_minutos(), ahora=momento
        ):
            registro.intentos_fallidos = 0
            registro.primer_intento_en = momento
            registro.ultimo_intento_en = momento
            registro.save()

        return False

    @classmethod
    def registrar_intento_fallido(cls, email: str, ip_address: str, ahora=None) -> IntentoAcceso:
        """Registra un intento fallido consecutivo para la combinación (cuenta, IP).

        - CA-05.1: Incrementa el contador dentro de la ventana de 15 minutos.
        - CA-05.2: Al alcanzar los 5 intentos fallidos consecutivos, activa el
          bloqueo temporal por 15 minutos para bloquear los intentos posteriores.
        """
        momento = ahora or timezone.now()
        email_norm = normalizar_email(email)
        ip_norm = (ip_address or '127.0.0.1').strip()

        with transaction.atomic():
            registro = cls.obtener_registro(email_norm, ip_norm)

            if registro is None:
                registro = IntentoAcceso(
                    email=email_norm,
                    ip_address=ip_norm,
                    intentos_fallidos=1,
                    primer_intento_en=momento,
                    ultimo_intento_en=momento,
                    bloqueado_hasta=None,
                )
            else:
                # Si el bloqueo previo ya expiró (CA-05.4) o la ventana de 15 min venció (CA-05.1)
                bloqueo_vencido = (
                    registro.bloqueado_hasta is not None
                    and not registro.esta_bloqueado(ahora=momento)
                )
                ventana_vencida = (
                    registro.bloqueado_hasta is None
                    and registro.ventana_expirada(cls.ventana_minutos(), ahora=momento)
                )

                if bloqueo_vencido or ventana_vencida or registro.intentos_fallidos == 0:
                    registro.intentos_fallidos = 1
                    registro.primer_intento_en = momento
                    registro.ultimo_intento_en = momento
                    registro.bloqueado_hasta = None
                else:
                    registro.intentos_fallidos += 1
                    registro.ultimo_intento_en = momento

            # CA-05.1 y CA-05.2: al alcanzar 5 intentos fallidos consecutivos en la
            # ventana de 15 minutos, los intentos posteriores quedan bloqueados por 15 minutos.
            if registro.intentos_fallidos >= cls.max_intentos() and not registro.esta_bloqueado(ahora=momento):
                registro.bloqueado_hasta = momento + timedelta(minutes=cls.tiempo_bloqueo_minutos())

            registro.save()
            return registro

    @classmethod
    def reiniciar_intentos(cls, email: str, ip_address: str, ahora=None) -> None:
        """CA-05.5: Un inicio de sesión exitoso reinicia el contador correspondiente."""
        momento = ahora or timezone.now()
        registro = cls.obtener_registro(email, ip_address)
        if registro is not None:
            registro.intentos_fallidos = 0
            registro.bloqueado_hasta = None
            registro.primer_intento_en = momento
            registro.ultimo_intento_en = momento
            registro.save()
