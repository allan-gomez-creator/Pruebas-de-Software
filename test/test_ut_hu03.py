"""
test/test_ut_hu03.py — PRUEBAS UNITARIAS DE HU-03 (Recuperación de contraseña).

Unidades probadas:
  1. Política de contraseña (CA-03.5): los validadores configurados en
     AUTH_PASSWORD_VALIDATORS (mínimo 8 caracteres + ComplejidadContrasenaValidator).
     Son las mismas reglas de HU-01 que usa el formulario de nueva contraseña.
  2. Vigencia del token de recuperación (CA-03.3, CA-03.4, CA-03.6): el generador
     de tokens de Django (PasswordResetTokenGenerator), que es el que usan las
     vistas de recuperación, con PASSWORD_RESET_TIMEOUT = 30 minutos.

Aislamiento (prueba unitaria pura):
  - No se usa la base de datos: el usuario se crea en memoria y nunca se guarda.
  - No se espera tiempo real: el reloj del generador se reemplaza por uno simulado,
    así se prueban 29 y 31 minutos en milisegundos.
  - No se envía ningún correo.

Ejecutar:  pytest test/test_ut_hu03.py
Patrón de cada prueba: Arrange (preparar) – Act (ejecutar) – Assert (verificar).
"""

from datetime import datetime, timedelta, timezone

import pytest
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError

from cuentas.models import Usuario


# =============================================================================
# Utilidades de las pruebas
# =============================================================================

def codigos_de_error(password):
    """Ejecuta la política de contraseña y devuelve los códigos de error.

    Devuelve un conjunto vacío si la contraseña es válida.
    """
    try:
        validate_password(password)
    except ValidationError as error:
        return {e.code for e in error.error_list}
    return set()


# Momento fijo de referencia: así las pruebas dan siempre el mismo resultado.
HORA_SOLICITUD = datetime(2026, 11, 4, 10, 0, 0)


class GeneradorConRelojSimulado(PasswordResetTokenGenerator):
    """Doble de prueba: el mismo generador de Django, pero con un reloj controlable.

    El generador real llama a self._now() para saber la hora. Aquí se reemplaza
    ese método para "mover el reloj" sin esperar.
    """

    def __init__(self, ahora):
        super().__init__()
        self.ahora = ahora

    def _now(self):
        return self.ahora


@pytest.fixture
def usuario_en_memoria():
    """Usuario de prueba que NO se guarda en la base de datos.

    El token solo depende de: id, hash de la contraseña, último login y correo.
    Se usa un hash ficticio para no gastar tiempo calculando PBKDF2.
    """
    return Usuario(
        pk=1,
        nombre='Ana',
        email='ana@prueba.com',
        password='hash-ficticio-de-la-contrasena-actual',
        last_login=datetime(2026, 11, 4, 9, 0, 0, tzinfo=timezone.utc),
    )


# =============================================================================
# HU-03 / CA-03.5 — Política de contraseña (UT-01 a UT-06)
# =============================================================================

def test_ut01_contrasena_de_7_caracteres_es_rechazada():
    """UT-01 · Límite inferior: 7 caracteres debe rechazarse (mínimo 8)."""
    # Arrange
    password = 'Abc1234'
    # Act
    errores = codigos_de_error(password)
    # Assert
    assert 'password_too_short' in errores


def test_ut02_contrasena_de_8_caracteres_es_aceptada():
    """UT-02 · Límite exacto: 8 caracteres con mayúscula, minúscula y número se acepta."""
    # Arrange
    password = 'Abcd1234'
    # Act
    errores = codigos_de_error(password)
    # Assert
    assert errores == set()


def test_ut03_contrasena_de_9_caracteres_es_aceptada():
    """UT-03 · Límite superior: 9 caracteres válidos se acepta."""
    # Arrange
    password = 'Abcde1234'
    # Act
    errores = codigos_de_error(password)
    # Assert
    assert errores == set()


def test_ut04_contrasena_sin_mayuscula_es_rechazada():
    """UT-04 · Negativo: sin letra mayúscula debe rechazarse."""
    # Arrange
    password = 'abcd1234'
    # Act
    errores = codigos_de_error(password)
    # Assert
    assert errores == {'sin_mayuscula'}


def test_ut05_contrasena_sin_minuscula_es_rechazada():
    """UT-05 · Negativo: sin letra minúscula debe rechazarse."""
    # Arrange
    password = 'ABCD1234'
    # Act
    errores = codigos_de_error(password)
    # Assert
    assert errores == {'sin_minuscula'}


def test_ut06_contrasena_sin_numero_es_rechazada():
    """UT-06 · Negativo: sin número debe rechazarse."""
    # Arrange
    password = 'Abcdefgh'
    # Act
    errores = codigos_de_error(password)
    # Assert
    assert errores == {'sin_numero'}


# =============================================================================
# HU-03 / CA-03.3, CA-03.4, CA-03.6 — Vigencia del token (UT-07 a UT-09)
# =============================================================================

def test_ut07_token_vigente_a_los_29_minutos(usuario_en_memoria):
    """UT-07 · Token vigente: a los 29 minutos de generado, el token es válido."""
    # Arrange: se genera el token a la hora de la solicitud
    token = GeneradorConRelojSimulado(HORA_SOLICITUD).make_token(usuario_en_memoria)
    reloj_29_min = GeneradorConRelojSimulado(HORA_SOLICITUD + timedelta(minutes=29))
    # Act
    es_valido = reloj_29_min.check_token(usuario_en_memoria, token)
    # Assert
    assert es_valido is True


def test_ut08_token_expirado_a_los_31_minutos(usuario_en_memoria):
    """UT-08 · Token expirado: a los 31 minutos de generado, el token ya no es válido."""
    # Arrange
    token = GeneradorConRelojSimulado(HORA_SOLICITUD).make_token(usuario_en_memoria)
    reloj_31_min = GeneradorConRelojSimulado(HORA_SOLICITUD + timedelta(minutes=31))
    # Act
    es_valido = reloj_31_min.check_token(usuario_en_memoria, token)
    # Assert
    assert es_valido is False


def test_ut09_token_consumido_tras_cambiar_la_contrasena(usuario_en_memoria):
    """UT-09 · Token consumido: después de cambiar la contraseña, el mismo token deja de servir.

    Al cambiar la contraseña cambia su hash, y el token depende de ese hash.
    Por eso el enlace es de un solo uso aunque siga dentro de los 30 minutos.
    """
    # Arrange
    generador = GeneradorConRelojSimulado(HORA_SOLICITUD + timedelta(minutes=5))
    token = generador.make_token(usuario_en_memoria)
    assert generador.check_token(usuario_en_memoria, token) is True  # válido antes del cambio
    # Act: se simula el cambio de contraseña que hace el formulario (solo en memoria)
    usuario_en_memoria.password = 'hash-ficticio-de-la-contrasena-nueva'
    # Assert
    assert generador.check_token(usuario_en_memoria, token) is False
