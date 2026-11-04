"""
test/test_ut_hu04.py — PRUEBAS UNITARIAS DE HU-04 (Cierre de sesión).

Unidades probadas:
  1. La función logout() de Django (CA-04.2): es la que ejecuta LogoutView al
     pulsar "Cerrar sesión". Decide invalidar la sesión (session.flush()) y deja
     al usuario como anónimo.
  2. SinCachePrivadasMiddleware (CA-04.4): agrega cabeceras para que el navegador
     no guarde las páginas privadas de un usuario autenticado.

Aislamiento (prueba unitaria pura):
  - La sesión es un objeto falso (Mock): así se comprueba que se pidió
    invalidarla sin tocar la base de datos donde Django guarda las sesiones.
  - La petición se crea con RequestFactory, sin servidor ni navegador.
  - La vista detrás del middleware es una función falsa que devuelve una respuesta vacía.

Ejecutar:  pytest test/test_ut_hu04.py
Patrón de cada prueba: Arrange (preparar) – Act (ejecutar) – Assert (verificar).
"""

from unittest.mock import Mock

import pytest
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory

from cuentas.middleware import SinCachePrivadasMiddleware


# =============================================================================
# Utilidades de las pruebas
# =============================================================================

class UsuarioAutenticadoFalso:
    """Doble de prueba: un usuario con sesión iniciada, sin base de datos."""
    is_authenticated = True
    is_anonymous = False


def peticion(usuario):
    """Crea una petición HTTP falsa con el usuario y una sesión falsa."""
    request = RequestFactory().get('/cuentas/panel/')
    request.user = usuario
    request.session = Mock()  # sesión falsa: registra qué métodos se le llaman
    return request


# =============================================================================
# HU-04 / CA-04.2 — Invalidación de la sesión (UT-10 a UT-12)
# =============================================================================

def test_ut10_cerrar_sesion_activa_invalida_la_sesion():
    """UT-10 · Sesión activa: al cerrar sesión se invalida la sesión y el usuario queda anónimo."""
    # Arrange
    request = peticion(UsuarioAutenticadoFalso())
    # Act
    logout(request)
    # Assert
    request.session.flush.assert_called_once()   # se pidió borrar la sesión en el servidor
    assert request.user.is_authenticated is False
    assert isinstance(request.user, AnonymousUser)


def test_ut11_cerrar_sesion_inexistente_no_genera_error():
    """UT-11 · Sesión inexistente: cerrar sesión sin haber iniciado no falla y sigue anónimo."""
    # Arrange
    request = peticion(AnonymousUser())
    # Act
    logout(request)   # si lanzara una excepción, la prueba fallaría aquí
    # Assert
    assert request.user.is_authenticated is False


def test_ut12_cerrar_sesion_dos_veces_no_genera_error():
    """UT-12 · Cierre repetido: cerrar sesión dos veces seguidas no falla."""
    # Arrange
    request = peticion(UsuarioAutenticadoFalso())
    # Act
    logout(request)
    logout(request)
    # Assert
    assert request.session.flush.call_count == 2
    assert request.user.is_authenticated is False


# =============================================================================
# HU-04 / CA-04.4 — Páginas privadas sin caché (UT-13 y UT-14)
# =============================================================================

def middleware_con_vista_falsa():
    """Crea el middleware con una vista falsa que siempre responde 200 vacío."""
    return SinCachePrivadasMiddleware(lambda request: HttpResponse('contenido'))


def test_ut13_respuesta_a_usuario_autenticado_no_se_guarda_en_cache():
    """UT-13 · Usuario autenticado: la respuesta lleva Cache-Control con no-store.

    Nota: esta prueba pasa, pero la prueba funcional CP-32 falló en Chrome por su
    back/forward cache. La prueba unitaria solo demuestra que la cabecera se envía;
    el criterio CA-04.4 completo necesita también la prueba funcional.
    """
    # Arrange
    middleware = middleware_con_vista_falsa()
    request = peticion(UsuarioAutenticadoFalso())
    # Act
    response = middleware(request)
    # Assert
    cache_control = response.headers.get('Cache-Control', '')
    assert 'no-store' in cache_control
    assert 'no-cache' in cache_control


def test_ut14_respuesta_a_usuario_anonimo_no_se_modifica():
    """UT-14 · Usuario anónimo: el middleware no agrega cabeceras de no-caché."""
    # Arrange
    middleware = middleware_con_vista_falsa()
    request = peticion(AnonymousUser())
    # Act
    response = middleware(request)
    # Assert
    assert 'Cache-Control' not in response.headers
