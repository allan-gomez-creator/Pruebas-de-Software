"""
test/test_hu05.py — PRUEBA SENCILLA CON PYTEST PARA HU-05.

Ejecutar en consola con:
    pytest
"""

from datetime import timedelta
import pytest
from django.utils import timezone

from cuentas.models import IntentoAcceso
from cuentas.services import LimitadorIntentosService


@pytest.mark.django_db
def test_bloqueo_al_quinto_intento_fallido():
    """CA-05.1 y CA-05.2: Al llegar a 5 intentos fallidos, la cuenta se bloquea."""
    correo = 'ana@test.local'
    ip = '127.0.0.1'

    # 1. Hacemos 4 intentos fallidos: aún NO debe estar bloqueada
    for _ in range(4):
        LimitadorIntentosService.registrar_intento_fallido(correo, ip)

    assert LimitadorIntentosService.esta_bloqueado(correo, ip) is False

    # 2. En el 5.º intento fallido: YA debe quedar bloqueada
    LimitadorIntentosService.registrar_intento_fallido(correo, ip)
    assert LimitadorIntentosService.esta_bloqueado(correo, ip) is True


@pytest.mark.django_db
def test_login_exitoso_reinicia_contador():
    """CA-05.5: Un inicio de sesión exitoso reinicia los intentos fallidos a 0."""
    correo = 'ana@test.local'
    ip = '127.0.0.1'

    # 1. Simulamos 3 fallos seguidos
    for _ in range(3):
        LimitadorIntentosService.registrar_intento_fallido(correo, ip)

    # 2. El usuario logra iniciar sesión -> se reinicia el contador
    LimitadorIntentosService.reiniciar_intentos(correo, ip)

    registro = IntentoAcceso.objects.get(email=correo, ip_address=ip)
    assert registro.intentos_fallidos == 0


@pytest.mark.django_db
def test_desbloqueo_despues_de_15_minutos():
    """CA-05.4: Después de 15 minutos el bloqueo termina automáticamente."""
    correo = 'ana@test.local'
    ip = '127.0.0.1'
    hace_16_minutos = timezone.now() - timedelta(minutes=16)

    # 1. Se bloqueó hace 16 minutos (5 intentos fallidos)
    for _ in range(5):
        LimitadorIntentosService.registrar_intento_fallido(correo, ip, ahora=hace_16_minutos)

    # 2. Como ya pasaron más de 15 minutos, ya NO está bloqueada
    assert LimitadorIntentosService.esta_bloqueado(correo, ip) is False
