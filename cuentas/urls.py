# cuentas/urls.py — RUTAS de la app cuentas.
# Relaciona cada URL con la vista que la atiende. Este archivo se "incluye"
# desde Sprint_1/urls.py bajo el prefijo /cuentas/.

from django.urls import path

from . import views                      # las funciones de cuentas/views.py

# Espacio de nombres: permite referirse a las rutas como 'cuentas:login',
# 'cuentas:registro', etc. Así no chocan con rutas de otras apps.
app_name = 'cuentas'

urlpatterns = [
    # path('<ruta>', <vista>, name='<nombre>')
    # El "name" se usa en redirect('cuentas:...') y en {% url 'cuentas:...' %}.
    path('registro/', views.registro, name='registro'),       # /cuentas/registro/ -> HU-01
    path('login/', views.iniciar_sesion, name='login'),        # /cuentas/login/    -> HU-02
    path('panel/', views.panel, name='panel'),                 # /cuentas/panel/    -> área privada
]