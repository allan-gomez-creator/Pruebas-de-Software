from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import TareaForm
from .models import Tarea


@login_required
def listar_tareas(request):
    """Leer: lista solo las tareas del usuario con sesion iniciada."""
    tareas = Tarea.objects.filter(usuario=request.user)
    return render(request, 'tareas/lista.html', {'tareas': tareas})


@login_required
def detalle_tarea(request, pk):
    """Leer: detalle de una tarea propia."""
    tarea = get_object_or_404(Tarea, pk=pk, usuario=request.user)
    return render(request, 'tareas/detalle.html', {'tarea': tarea})


@login_required
@require_http_methods(['GET', 'POST'])
def crear_tarea(request):
    """Crear: la tarea queda asociada al usuario autenticado."""
    form = TareaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tarea = form.save(commit=False)
        tarea.usuario = request.user
        tarea.save()
        messages.success(request, f'Tarea "{tarea.nombre}" creada con éxito.')
        return redirect('tareas:lista')
    return render(request, 'tareas/formulario.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def eliminar_tarea(request, pk):
    """Eliminar: GET muestra la confirmacion, POST borra."""
    tarea = get_object_or_404(Tarea, pk=pk, usuario=request.user)
    if request.method == 'POST':
        nombre = tarea.nombre
        tarea.delete()
        messages.success(request, f'Tarea "{nombre}" eliminada.')
        return redirect('tareas:lista')
    return render(request, 'tareas/confirmar_eliminar.html', {'tarea': tarea})