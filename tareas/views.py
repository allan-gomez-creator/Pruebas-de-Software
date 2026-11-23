import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import TareaForm
from .models import Tarea

MESES_ES = (
    '',
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
)
DIAS_SEMANA_ES = ('Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom')


def _mes_anterior_y_siguiente(anio: int, mes: int):
    """Calcula las tuplas (año, mes) del mes anterior y del mes siguiente."""
    ant = (anio - 1, 12) if mes == 1 else (anio, mes - 1)
    sig = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return ant, sig


def _obtener_anio_mes(request, tareas_qs):
    """Determina el año y mes a mostrar en el calendario.

    Si vienen `?anio=YYYY&mes=MM` válidos en la URL, usa esos.
    Si no vienen y el usuario tiene tareas, posiciona el calendario en el mes
    de la primera tarea para que siempre sea visible de inmediato (CA-03 / CA-06);
    en caso contrario usa la fecha actual.
    """
    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get('anio', ''))
        mes = int(request.GET.get('mes', ''))
        if 1 <= mes <= 12 and 1970 <= anio <= 2100:
            return anio, mes
    except (TypeError, ValueError):
        pass

    primera = tareas_qs.first()
    if primera is not None:
        return primera.fecha_inicio.year, primera.fecha_inicio.month
    return hoy.year, hoy.month


def construir_calendario_mensual(tareas, anio: int, mes: int):
    """Construye la cuadrícula semanal del mes con las tareas dentro de su rango de fechas (CA-03 y CA-06)."""
    cal = calendar.Calendar(firstweekday=0)
    hoy = timezone.localdate()
    lista_tareas = list(tareas)
    semanas = []

    for semana in cal.monthdatescalendar(anio, mes):
        fila = []
        for fecha_dia in semana:
            tareas_dia = [
                t for t in lista_tareas
                if t.fecha_inicio <= fecha_dia <= t.fecha_fin
            ]
            fila.append({
                'fecha': fecha_dia,
                'dia': fecha_dia.day,
                'en_mes': fecha_dia.month == mes,
                'es_hoy': fecha_dia == hoy,
                'tareas': tareas_dia,
            })
        semanas.append(fila)

    (ant_anio, ant_mes), (sig_anio, sig_mes) = _mes_anterior_y_siguiente(anio, mes)
    return {
        'anio': anio,
        'mes': mes,
        'nombre_mes': MESES_ES[mes],
        'dias_semana': DIAS_SEMANA_ES,
        'semanas': semanas,
        'ant_anio': ant_anio,
        'ant_mes': ant_mes,
        'sig_anio': sig_anio,
        'sig_mes': sig_mes,
        'hoy': date(hoy.year, hoy.month, 1),
    }


@login_required
def listar_tareas(request):
    """Leer: lista solo las tareas del usuario con sesión iniciada y las muestra en el calendario (CA-03 y CA-06)."""
    tareas = Tarea.objects.filter(usuario=request.user)
    anio, mes = _obtener_anio_mes(request, tareas)
    calendario = construir_calendario_mensual(tareas, anio, mes)
    return render(
        request,
        'tareas/lista.html',
        {
            'tareas': tareas,
            'calendario': calendario,
        },
    )


@login_required
def calendario_tareas(request):
    """Vista dedicada del calendario mensual con las tareas en su rango de fechas (CA-03 y CA-06)."""
    tareas = Tarea.objects.filter(usuario=request.user)
    anio, mes = _obtener_anio_mes(request, tareas)
    calendario = construir_calendario_mensual(tareas, anio, mes)
    return render(
        request,
        'tareas/calendario.html',
        {
            'tareas': tareas,
            'calendario': calendario,
        },
    )


@login_required
def detalle_tarea(request, pk):
    """Leer: detalle de una tarea propia (CA-04)."""
    tarea = get_object_or_404(Tarea, pk=pk, usuario=request.user)
    return render(request, 'tareas/detalle.html', {'tarea': tarea})


@login_required
@require_http_methods(['GET', 'POST'])
def crear_tarea(request):
    """Crear: la tarea queda asociada al usuario autenticado (CA-01, CA-02, CA-03)."""
    form = TareaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tarea = form.save(commit=False)
        tarea.usuario = request.user
        tarea.save()
        messages.success(request, f'Tarea "{tarea.nombre}" creada con éxito.')
        return redirect('tareas:lista')
    return render(request, 'tareas/formulario.html', {'form': form, 'modo_edicion': False})


@login_required
@require_http_methods(['GET', 'POST'])
def editar_tarea(request, pk):
    """Actualizar: modifica nombre, descripción, fechas y estado de una tarea existente propia (CA-05 y CA-06)."""
    tarea = get_object_or_404(Tarea, pk=pk, usuario=request.user)
    form = TareaForm(request.POST or None, instance=tarea)
    if request.method == 'POST' and form.is_valid():
        tarea_actualizada = form.save()
        messages.success(request, f'Tarea "{tarea_actualizada.nombre}" actualizada con éxito.')
        return redirect('tareas:lista')
    return render(
        request,
        'tareas/formulario.html',
        {
            'form': form,
            'tarea': tarea,
            'modo_edicion': True,
        },
    )


@login_required
@require_http_methods(['GET', 'POST'])
def eliminar_tarea(request, pk):
    """Eliminar: GET muestra la confirmación, POST borra (CA-07 y CA-08)."""
    tarea = get_object_or_404(Tarea, pk=pk, usuario=request.user)
    if request.method == 'POST':
        nombre = tarea.nombre
        tarea.delete()
        messages.success(request, f'Tarea "{nombre}" eliminada.')
        return redirect('tareas:lista')
    return render(request, 'tareas/confirmar_eliminar.html', {'tarea': tarea})
