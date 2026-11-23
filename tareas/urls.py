from django.urls import path

from . import views

app_name = 'tareas'

urlpatterns = [
    path('', views.listar_tareas, name='lista'),
    path('nueva/', views.crear_tarea, name='crear'),
    path('<int:pk>/', views.detalle_tarea, name='detalle'),
    path('<int:pk>/eliminar/', views.eliminar_tarea, name='eliminar'),
]