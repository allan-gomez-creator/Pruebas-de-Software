# Sprint_1/urls.py — RUTAS PRINCIPALES del proyecto.
# Django revisa esta lista de arriba a abajo y usa la primera ruta que
# coincida con la URL que pidió el navegador.

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView     # vista lista para hacer redirecciones

from despliegue import views                      # vistas del "Hola Mundo" original

urlpatterns = [
    # Panel de administración de Django.
    path('admin/', admin.site.urls),

    # Todo lo que empiece por /cuentas/ lo resuelve cuentas/urls.py
    # (módulo de autenticación: HU-01, HU-02 y las siguientes).
    path('cuentas/', include('cuentas.urls')),

    # La raíz (http://127.0.0.1:8000/) redirige al inicio de sesión.
    # permanent=False -> redirección temporal (302), el navegador no la memoriza.
    path('', RedirectView.as_view(pattern_name='cuentas:login', permanent=False)),

    # Páginas de ejemplo del framework original (se movió el "Hola Mundo" a /hola/).
    path('hola/', views.hello),
    path('about/', views.about),
]