from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from despliegue import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuentas/', include('cuentas.urls')),
    path('tareas/', include('tareas.urls')),
    path('', RedirectView.as_view(pattern_name='cuentas:login', permanent=False)),
    path('hola/', views.hello),
    path('about/', views.about),
]