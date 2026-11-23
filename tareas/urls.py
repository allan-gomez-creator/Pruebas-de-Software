from django.urls import path

from . import views

app_name = 'tareas'

urlpatterns = [
    path('', views.listar_tareas, name='lista'),
    path('calendario/', views.calendario_tareas, name='calendario'),
    path('nueva/', views.crear_tarea, name='crear'),
    path('<int:pk>/', views.detalle_tarea, name='detalle'),
    path('<int:pk>/editar/', views.editar_tarea, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_tarea, name='eliminar'),
]
