"""
test/test_ut_hu05.py — PRUEBAS UNITARIAS DE HU-05 (Límite de intentos fallidos).

Unidad probada: LimitadorIntentosService (cuentas/services.py), que cuenta los
intentos fallidos por combinación de cuenta + IP y decide el bloqueo temporal.

Aislamiento (prueba unitaria pura):
  - Repositorio falso: en vez de consultar la tabla IntentoAcceso en la base de
    datos, los registros se guardan en un diccionario en memoria.
  - Reloj simulado: cada llamada recibe la hora con el parámetro `ahora`, así se
    prueban 15 minutos sin esperar.
  - Configuración fija: 5 intentos, ventana de 15 min y bloqueo de 15 min, para
    que el resultado no dependa de variables de entorno.

Reto de equipo (diapositiva 23) — qué cambio en el código haría fallar estas pruebas:
  - Si en services.py se cambia `intentos_fallidos >= cls.max_intentos()` por `>`,
    el bloqueo llegaría en el 6.º fallo y fallaría UT-16.
  - Si el máximo de intentos se cambia de 5 a 4, fallaría UT-15.
  - Si se quita la condición `not registro.esta_bloqueado(...)`, cada fallo durante
    el bloqueo lo alargaría y fallaría UT-17.

Ejecutar:  pytest test/test_ut_hu05.py
Patrón de cada prueba: Arrange (preparar) – Act (ejecutar) – Assert (verificar).
"""

from contextlib import nullcontext
from datetime import datetime, timedelta, timezone

import pytest

from cuentas.models import IntentoAcceso, normalizar_email
from cuentas.services import LimitadorIntentosService as Limitador


CORREO = 'ana@prueba.com'
IP_A = '127.0.0.1'
IP_B = '10.0.0.2'
T0 = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)   # hora del primer intento


# =============================================================================
# Dobles de prueba (aislamiento de la base de datos y de la configuración)
# =============================================================================

@pytest.fixture(autouse=True)
def politica_fija(settings):
    """Fija la política de CA-05.1 y CA-05.2 durante cada prueba."""
    settings.AUTH_MAX_INTENTOS_FALLIDOS = 5
    settings.AUTH_VENTANA_INTENTOS_MINUTOS = 15
    settings.AUTH_TIEMPO_BLOQUEO_MINUTOS = 15


@pytest.fixture(autouse=True)
def repositorio_en_memoria(monkeypatch):
    """Reemplaza la base de datos por un diccionario {(correo, ip): registro}."""
    almacen = {}

    def obtener_registro(cls, email, ip_address):
        return almacen.get((normalizar_email(email), ip_address))

    def guardar(registro, *args, **kwargs):
        registro.email = normalizar_email(registro.email)
        almacen[(registro.email, registro.ip_address)] = registro

    monkeypatch.setattr(Limitador, 'obtener_registro', classmethod(obtener_registro))
    monkeypatch.setattr(IntentoAcceso, 'save', guardar)
    monkeypatch.setattr('cuentas.services.transaction.atomic', nullcontext)
    return almacen


def fallar(veces, desde=T0, ip=IP_A, cada_segundos=10):
    """Registra `veces` intentos fallidos seguidos y devuelve el último registro."""
    registro = None
    for i in range(veces):
        registro = Limitador.registrar_intento_fallido(
            CORREO, ip, ahora=desde + timedelta(seconds=i * cada_segundos)
        )
    return registro


# =============================================================================
# HU-05 / CA-05.1 y CA-05.2 — 4, 5 y 6 intentos fallidos (UT-15 a UT-17)
# =============================================================================

def test_ut15_cuatro_fallos_no_bloquean():
    """UT-15 · 4 fallos: todavía no se bloquea (el límite es 5)."""
    # Arrange y Act
    registro = fallar(4)
    # Assert
    assert registro.intentos_fallidos == 4
    assert Limitador.esta_bloqueado(CORREO, IP_A, ahora=T0 + timedelta(minutes=1)) is False


def test_ut16_quinto_fallo_bloquea_por_15_minutos():
    """UT-16 · 5 fallos: se activa el bloqueo, que dura 15 minutos desde el 5.º fallo."""
    # Arrange
    hora_quinto_fallo = T0 + timedelta(seconds=40)   # fallar() deja 10 s entre intentos
    # Act
    registro = fallar(5)
    # Assert
    assert registro.intentos_fallidos == 5
    assert registro.bloqueado_hasta == hora_quinto_fallo + timedelta(minutes=15)
    assert Limitador.esta_bloqueado(CORREO, IP_A, ahora=hora_quinto_fallo) is True


def test_ut17_sexto_fallo_sigue_bloqueado_y_no_alarga_el_bloqueo():
    """UT-17 · 6 fallos: sigue bloqueado y el 6.º intento no extiende el bloqueo."""
    # Arrange
    bloqueo_original = fallar(5).bloqueado_hasta
    # Act: 6.º intento fallido 1 minuto después
    registro = Limitador.registrar_intento_fallido(CORREO, IP_A, ahora=T0 + timedelta(minutes=1))
    # Assert
    assert registro.intentos_fallidos == 6
    assert registro.bloqueado_hasta == bloqueo_original
    assert Limitador.esta_bloqueado(CORREO, IP_A, ahora=T0 + timedelta(minutes=1)) is True


# =============================================================================
# HU-05 / CA-05.2 — Bloqueo vigente y expirado (UT-18 y UT-19)
# =============================================================================

def test_ut18_bloqueo_vigente_a_los_14_min_59_s():
    """UT-18 · Bloqueo vigente: 1 segundo antes de cumplir los 15 minutos sigue bloqueado."""
    # Arrange
    bloqueado_hasta = fallar(5).bloqueado_hasta
    # Act
    bloqueado = Limitador.esta_bloqueado(CORREO, IP_A, ahora=bloqueado_hasta - timedelta(seconds=1))
    # Assert
    assert bloqueado is True


def test_ut19_bloqueo_expirado_a_los_15_minutos_reinicia_el_contador():
    """UT-19 · Bloqueo expirado: al cumplir los 15 minutos se desbloquea y el contador vuelve a 0."""
    # Arrange
    registro = fallar(5)
    # Act
    bloqueado = Limitador.esta_bloqueado(CORREO, IP_A, ahora=registro.bloqueado_hasta)
    # Assert
    assert bloqueado is False
    assert registro.intentos_fallidos == 0
    assert registro.bloqueado_hasta is None


# =============================================================================
# HU-05 / CA-05.1 y CA-05.4 — Ventana, reinicio y aislamiento (UT-20 a UT-22)
# =============================================================================

def test_ut20_fallos_fuera_de_la_ventana_de_15_minutos_no_se_acumulan():
    """UT-20 · Ventana: 3 fallos, 16 minutos de espera y 3 fallos más no bloquean."""
    # Arrange
    fallar(3, desde=T0)
    # Act
    registro = fallar(3, desde=T0 + timedelta(minutes=16))
    # Assert: el conteo empezó de nuevo
    assert registro.intentos_fallidos == 3
    assert registro.bloqueado_hasta is None


def test_ut21_inicio_de_sesion_exitoso_reinicia_el_contador():
    """UT-21 · Reinicio (CA-05.4): 4 fallos, login exitoso y 4 fallos más no bloquean."""
    # Arrange
    fallar(4, desde=T0)
    Limitador.reiniciar_intentos(CORREO, IP_A, ahora=T0 + timedelta(minutes=1))
    # Act
    registro = fallar(4, desde=T0 + timedelta(minutes=2))
    # Assert
    assert registro.intentos_fallidos == 4
    assert registro.bloqueado_hasta is None


def test_ut22_el_bloqueo_aplica_solo_a_la_combinacion_cuenta_e_ip():
    """UT-22 · Aislamiento: bloquear la cuenta en la IP A no bloquea la misma cuenta en la IP B."""
    # Arrange
    fallar(5, ip=IP_A)
    momento = T0 + timedelta(minutes=1)
    # Act
    bloqueado_en_a = Limitador.esta_bloqueado(CORREO, IP_A, ahora=momento)
    bloqueado_en_b = Limitador.esta_bloqueado(CORREO, IP_B, ahora=momento)
    # Assert
    assert bloqueado_en_a is True
    assert bloqueado_en_b is False
