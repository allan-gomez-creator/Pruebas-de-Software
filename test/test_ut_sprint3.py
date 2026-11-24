"""
test/test_ut_sprint3.py — PRUEBAS UNITARIAS DE CAJA BLANCA · SPRINT 3 (Gestión de tareas).

Métodos probados (4):
  M1. TareaForm.clean()                 tareas/forms.py   Validación de fechas al crear/editar.
  M2. _obtener_anio_mes()               tareas/views.py   Qué mes muestra el calendario.
  M3. construir_calendario_mensual()    tareas/views.py   Arma la cuadrícula del mes con las tareas.
  M4. eliminar_tarea()                  tareas/views.py   Borrado de una tarea (confirmación y POST).

Técnica: caja blanca por CAMINOS BÁSICOS (McCabe). Para cada método se dibujó su
grafo de flujo, se calculó la complejidad ciclomática V(G) y se escribió una
prueba por cada camino independiente (ver el Excel "Pruebas_Sprint3.xlsx").
Cada prueba indica en su docstring el camino que recorre (C1, C2, ...).

Aislamiento:
  - M2 y M3 no usan base de datos: la petición se crea con RequestFactory, las
    tareas son objetos falsos y el reloj ("hoy") se reemplaza por una fecha fija.
  - M1 y M4 usan la base de datos de PRUEBA que pytest crea y borra sola
    (marca django_db). Nunca tocan la base de datos real del proyecto.

Ejecutar:   pytest test/test_ut_sprint3.py -v
Patrón de cada prueba: Arrange (preparar) – Act (ejecutar) – Assert (verificar).
"""

from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.contrib.messages import get_messages
from django.test import RequestFactory
from django.urls import reverse

from tareas.forms import TareaForm
from tareas.models import EstadoTarea, Tarea
from tareas.views import _obtener_anio_mes, construir_calendario_mensual


# =============================================================================
# Utilidades de las pruebas
# =============================================================================

HOY_SIMULADO = date(2026, 11, 23)   # "hoy" fijo: las pruebas dan siempre el mismo resultado


@pytest.fixture
def reloj_fijo(monkeypatch):
    """Doble de prueba: hace que timezone.localdate() devuelva siempre HOY_SIMULADO."""
    monkeypatch.setattr('tareas.views.timezone.localdate', lambda: HOY_SIMULADO)
    return HOY_SIMULADO


def datos_tarea(**cambios):
    """Datos válidos del formulario; cada prueba cambia solo lo que le interesa."""
    datos = {
        'nombre': 'Entregar informe',
        'descripcion': 'Informe final',
        'fecha_inicio': '2026-11-20',
        'fecha_fin': '2026-11-25',
        'estado': EstadoTarea.PENDIENTE,
    }
    datos.update(cambios)
    return datos


class ConsultaFalsa:
    """Doble de prueba de un QuerySet: solo implementa .first(), que es lo que usa M2."""

    def __init__(self, tareas):
        self._tareas = list(tareas)

    def first(self):
        return self._tareas[0] if self._tareas else None


def tarea_falsa(inicio, fin, nombre='Tarea'):
    """Tarea en memoria (sin base de datos) con lo que lee el calendario."""
    return SimpleNamespace(nombre=nombre, fecha_inicio=inicio, fecha_fin=fin)


def peticion(query=''):
    """Petición GET falsa a la página del calendario con los parámetros dados."""
    return RequestFactory().get('/tareas/calendario/' + (f'?{query}' if query else ''))


MENSAJE_FECHAS = 'La fecha de fin no puede ser anterior a la fecha de inicio.'


# =============================================================================
# M1 · TareaForm.clean()  —  V(G) = 4  →  4 caminos
# =============================================================================

@pytest.mark.django_db
def test_ut23_clean_sin_fecha_inicio_no_compara_fechas():
    """UT-23 · Camino C1 (1-2-6): falta la fecha de inicio.

    La condición `inicio` es falsa, así que clean() no compara fechas: solo debe
    quedar el error de campo obligatorio, nunca el de fechas invertidas.
    """
    # Arrange
    form = TareaForm(data=datos_tarea(fecha_inicio=''))
    # Act
    valido = form.is_valid()
    # Assert
    assert valido is False
    assert form.errors['fecha_inicio'] == ['La fecha de inicio es obligatoria.']
    assert 'fecha_fin' not in form.errors


@pytest.mark.django_db
def test_ut24_clean_sin_fecha_fin_no_compara_fechas():
    """UT-24 · Camino C2 (1-2-3-6): hay fecha de inicio pero falta la de fin."""
    # Arrange
    form = TareaForm(data=datos_tarea(fecha_fin=''))
    # Act
    valido = form.is_valid()
    # Assert
    assert valido is False
    assert form.errors['fecha_fin'] == ['La fecha de fin es obligatoria.']
    assert MENSAJE_FECHAS not in form.errors['fecha_fin']


@pytest.mark.django_db
def test_ut25_clean_fin_igual_a_inicio_es_valida():
    """UT-25 · Camino C3 (1-2-3-4-6) con VALOR LÍMITE: fin == inicio.

    `fin < inicio` es falso en el límite exacto, así que la tarea de un solo día
    es válida.
    """
    # Arrange
    form = TareaForm(data=datos_tarea(fecha_inicio='2026-11-20', fecha_fin='2026-11-20'))
    # Act
    valido = form.is_valid()
    # Assert
    assert valido is True, form.errors
    assert form.cleaned_data['fecha_fin'] == date(2026, 11, 20)


@pytest.mark.django_db
def test_ut26_clean_fin_un_dia_antes_de_inicio_es_rechazada():
    """UT-26 · Camino C4 (1-2-3-4-5-6) con VALOR LÍMITE: fin = inicio − 1 día.

    Es el caso más cercano al límite que debe fallar: se agrega el error a
    fecha_fin y el campo sale de cleaned_data.
    """
    # Arrange
    form = TareaForm(data=datos_tarea(fecha_inicio='2026-11-20', fecha_fin='2026-11-19'))
    # Act
    valido = form.is_valid()
    # Assert
    assert valido is False
    assert form.errors['fecha_fin'] == [MENSAJE_FECHAS]
    assert 'fecha_fin' not in form.cleaned_data


# =============================================================================
# M2 · _obtener_anio_mes()  —  V(G) = 4  →  4 caminos (+ valores frontera)
# =============================================================================

def test_ut27_anio_mes_validos_en_la_url(reloj_fijo):
    """UT-27 · Camino C1 (1-2-3-4-10): ?anio=2027&mes=5 válidos → se usan tal cual."""
    # Arrange
    tareas = ConsultaFalsa([tarea_falsa(date(2026, 1, 10), date(2026, 1, 12))])
    # Act
    resultado = _obtener_anio_mes(peticion('anio=2027&mes=5'), tareas)
    # Assert
    assert resultado == (2027, 5)


def test_ut28_parametros_numericos_fuera_de_rango_sin_tareas_usa_hoy(reloj_fijo):
    """UT-28 · Camino C2 (1-2-3-6-7-9-10): mes=13 es número pero está fuera de rango.

    No hay excepción, el `if` de rango es falso y, como no hay tareas, se usa el
    mes actual. Este camino NO lo cubrían las pruebas del equipo (coverage
    marcaba la rama 40->45 como parcial).
    """
    # Arrange
    tareas = ConsultaFalsa([])
    # Act
    resultado = _obtener_anio_mes(peticion('anio=2026&mes=13'), tareas)
    # Assert
    assert resultado == (2026, 11)


def test_ut29_sin_parametros_con_tareas_usa_mes_de_la_primera(reloj_fijo):
    """UT-29 · Camino C3 (1-2-5-6-7-8-10): sin parámetros → int('') lanza ValueError.

    Se captura la excepción y, como hay tareas, el calendario se posiciona en el
    mes de la primera tarea (CA-03 / CA-06).
    """
    # Arrange
    tareas = ConsultaFalsa([tarea_falsa(date(2027, 3, 4), date(2027, 3, 9))])
    # Act
    resultado = _obtener_anio_mes(peticion(), tareas)
    # Assert
    assert resultado == (2027, 3)


def test_ut30_parametros_no_numericos_sin_tareas_usa_hoy(reloj_fijo):
    """UT-30 · Camino C4 (1-2-5-6-7-9-10): ?anio=abc → ValueError y sin tareas → hoy."""
    # Arrange
    tareas = ConsultaFalsa([])
    # Act
    resultado = _obtener_anio_mes(peticion('anio=abc&mes=5'), tareas)
    # Assert
    assert resultado == (2026, 11)


@pytest.mark.parametrize('anio, mes, aceptado', [
    (2026, 1, True),  (2026, 12, True),     # límites de mes válidos
    (2026, 0, False), (2026, 13, False),    # justo afuera
    (1970, 6, True),  (2100, 6, True),      # límites de año válidos
    (1969, 6, False), (2101, 6, False),     # justo afuera
])
def test_ut31_valores_frontera_del_rango(reloj_fijo, anio, mes, aceptado):
    """UT-31 · Nodo 3 (condición compuesta): análisis de valores frontera.

    La condición `1 <= mes <= 12 and 1970 <= anio <= 2100` tiene 4 comparaciones;
    se prueba cada límite y el valor justo afuera de él.
    """
    # Arrange
    tareas = ConsultaFalsa([])
    # Act
    resultado = _obtener_anio_mes(peticion(f'anio={anio}&mes={mes}'), tareas)
    # Assert
    esperado = (anio, mes) if aceptado else (2026, 11)
    assert resultado == esperado


# =============================================================================
# M3 · construir_calendario_mensual()  —  V(G) = 5  →  5 caminos
# =============================================================================

def test_ut32_mes_sin_tareas_arma_semanas_completas(reloj_fijo):
    """UT-32 · Camino C3 (1-2-3-4-5-8-4-9-2-10): no hay tareas, así que el ciclo
    de tareas (nodo 5) termina de inmediato en cada día del mes.

    Los caminos C1 (mes sin semanas) y C2 (semana sin días) NO son ejecutables:
    calendar.monthdatescalendar() siempre devuelve semanas completas de 7 días.

    Cada semana debe tener 7 días, empezar en lunes, y ningún día tiene tareas.
    """
    # Arrange
    tareas = []
    # Act
    cal = construir_calendario_mensual(tareas, 2026, 11)
    # Assert
    assert len(cal['semanas']) >= 4
    for semana in cal['semanas']:
        assert len(semana) == 7
        assert semana[0]['fecha'].weekday() == 0      # lunes
        assert all(dia['tareas'] == [] for dia in semana)
    dias_del_mes = [d for s in cal['semanas'] for d in s if d['en_mes']]
    assert len(dias_del_mes) == 30                    # noviembre tiene 30 días


def test_ut33_tarea_aparece_solo_dentro_de_su_rango(reloj_fijo):
    """UT-33 · Caminos C4 (5-6-5: tarea fuera del rango del día) y C5 (5-6-7-5: tarea
    dentro del rango), con VALORES LÍMITE.

    Tarea del 20 al 25: debe aparecer el 20 y el 25 (límites incluidos) y NO el
    19 ni el 26 (justo afuera).
    """
    # Arrange
    tarea = tarea_falsa(date(2026, 11, 20), date(2026, 11, 25), 'Informe')
    # Act
    cal = construir_calendario_mensual([tarea], 2026, 11)
    # Assert
    por_fecha = {d['fecha']: d['tareas'] for s in cal['semanas'] for d in s}
    assert por_fecha[date(2026, 11, 20)] == [tarea]
    assert por_fecha[date(2026, 11, 25)] == [tarea]
    assert por_fecha[date(2026, 11, 19)] == []
    assert por_fecha[date(2026, 11, 26)] == []
    dias_con_tarea = [f for f, t in por_fecha.items() if t]
    assert len(dias_con_tarea) == 6                   # del 20 al 25 inclusive


def test_ut34_marca_dias_de_otro_mes_y_el_dia_de_hoy(reloj_fijo):
    """UT-34 · Nodo 8: datos que se guardan de cada día (en_mes / es_hoy).

    Noviembre 2026 empieza en domingo, así que la primera fila trae días de
    octubre (en_mes = False). Solo el 23 de noviembre (hoy simulado) es "hoy";
    en octubre ningún día es "hoy", aunque exista un 23 de octubre.
    """
    # Arrange / Act
    cal = construir_calendario_mensual([], 2026, 11)
    cal_octubre = construir_calendario_mensual([], 2026, 10)
    # Assert
    primer_dia = cal['semanas'][0][0]
    assert primer_dia['fecha'] == date(2026, 10, 26)
    assert primer_dia['en_mes'] is False
    dias_hoy = [d['fecha'] for s in cal['semanas'] for d in s if d['es_hoy']]
    assert dias_hoy == [HOY_SIMULADO]
    assert not any(d['es_hoy'] for s in cal_octubre['semanas'] for d in s)


def test_ut35_diciembre_navega_a_enero_del_anio_siguiente(reloj_fijo):
    """UT-35 · Nodo 10: al terminar las semanas se calcula la navegación entre meses.

    En diciembre, "mes siguiente" debe ser enero del año siguiente.
    """
    # Arrange / Act
    cal = construir_calendario_mensual([], 2026, 12)
    # Assert
    assert cal['nombre_mes'] == 'Diciembre'
    assert (cal['ant_anio'], cal['ant_mes']) == (2026, 11)
    assert (cal['sig_anio'], cal['sig_mes']) == (2027, 1)
    assert cal['hoy'] == date(2026, 11, 1)


# =============================================================================
# M4 · eliminar_tarea()  —  V(G) = 5  →  5 caminos
# =============================================================================

@pytest.fixture
def usuarios(django_user_model, settings):
    """Dos usuarios de prueba: el dueño de la tarea y otra persona."""
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    duenio = django_user_model.objects.create_user('duenio@prueba.com', 'Dueño', 'Abc12345')
    otro = django_user_model.objects.create_user('otro@prueba.com', 'Otro', 'Abc12345')
    return duenio, otro


@pytest.fixture
def tarea(usuarios):
    duenio, _ = usuarios
    return Tarea.objects.create(
        usuario=duenio, nombre='Estudiar', descripcion='',
        fecha_inicio=date(2026, 11, 20), fecha_fin=date(2026, 11, 21),
    )


@pytest.mark.django_db
def test_ut36_eliminar_sin_sesion_redirige_al_login(client, tarea):
    """UT-36 · Camino C1 (1-2-10): @login_required corta antes de la vista."""
    # Arrange
    url = reverse('tareas:eliminar', args=[tarea.pk])
    # Act
    respuesta = client.post(url)
    # Assert
    assert respuesta.status_code == 302
    assert reverse('cuentas:login') in respuesta['Location']
    assert Tarea.objects.filter(pk=tarea.pk).exists()


@pytest.mark.django_db
def test_ut37_eliminar_con_metodo_no_permitido_da_405(client, usuarios, tarea):
    """UT-37 · Camino C2 (1-3-4-10): @require_http_methods solo deja GET y POST."""
    # Arrange
    client.force_login(usuarios[0])
    url = reverse('tareas:eliminar', args=[tarea.pk])
    # Act
    respuesta = client.delete(url)
    # Assert
    assert respuesta.status_code == 405
    assert Tarea.objects.filter(pk=tarea.pk).exists()


@pytest.mark.django_db
def test_ut38_eliminar_tarea_ajena_da_404_y_no_la_borra(client, usuarios, tarea):
    """UT-38 · Camino C3 (1-3-5-6-10): get_object_or_404 filtra por usuario."""
    # Arrange
    client.force_login(usuarios[1])                   # NO es el dueño
    url = reverse('tareas:eliminar', args=[tarea.pk])
    # Act
    respuesta = client.post(url)
    # Assert
    assert respuesta.status_code == 404
    assert Tarea.objects.filter(pk=tarea.pk).exists()


@pytest.mark.django_db
def test_ut39_eliminar_con_get_pide_confirmacion(client, usuarios, tarea):
    """UT-39 · Camino C4 (1-3-5-7-9-10): GET muestra la confirmación y no borra (CA-07)."""
    # Arrange
    client.force_login(usuarios[0])
    url = reverse('tareas:eliminar', args=[tarea.pk])
    # Act
    respuesta = client.get(url)
    # Assert
    assert respuesta.status_code == 200
    assert 'tareas/confirmar_eliminar.html' in [t.name for t in respuesta.templates]
    assert Tarea.objects.filter(pk=tarea.pk).exists()


@pytest.mark.django_db
def test_ut40_eliminar_con_post_borra_y_redirige(client, usuarios, tarea):
    """UT-40 · Camino C5 (1-3-5-7-8-10): POST borra, avisa y vuelve al listado (CA-07, CA-08)."""
    # Arrange
    client.force_login(usuarios[0])
    url = reverse('tareas:eliminar', args=[tarea.pk])
    # Act
    respuesta = client.post(url)
    # Assert
    assert respuesta.status_code == 302
    assert respuesta['Location'] == reverse('tareas:lista')
    assert not Tarea.objects.filter(pk=tarea.pk).exists()
    mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
    assert mensajes == ['Tarea "Estudiar" eliminada.']


# =============================================================================
# DEFECTO ENCONTRADO CON CAJA BLANCA (DEF-01)
# =============================================================================

@pytest.mark.xfail(strict=True, reason='DEF-01: la navegación del calendario sale del rango 1970-2100')
def test_ut41_def01_mes_siguiente_a_diciembre_2100_es_navegable(reloj_fijo):
    """UT-41 · DEF-01 (falla esperada, marcada con xfail).

    El calendario acepta años de 1970 a 2100 (M2, nodo 3), pero M3 genera el
    enlace "Mes siguiente" de diciembre 2100 hacia enero 2101 sin revisar ese
    rango. Al pulsarlo, M2 rechaza 2101 y el usuario salta al mes actual.

    Esperado: el enlace se desactiva (sig_anio = None) o lleva a un mes que el
    calendario sí acepta. Cuando el equipo corrija el defecto, esta prueba
    pasará y pytest avisará (XPASS estricto) para quitar la marca xfail.
    """
    # Arrange
    cal = construir_calendario_mensual([], 2100, 12)
    # Act
    if cal['sig_anio'] is None:
        return
    destino = _obtener_anio_mes(
        peticion(f"anio={cal['sig_anio']}&mes={cal['sig_mes']}"), ConsultaFalsa([])
    )
    # Assert
    assert destino == (cal['sig_anio'], cal['sig_mes'])
