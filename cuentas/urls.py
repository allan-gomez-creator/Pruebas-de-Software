# cuentas/urls.py — RUTAS de la app cuentas.
# Relaciona cada URL con la vista que la atiende. Este archivo se "incluye"
# desde Sprint_1/urls.py bajo el prefijo /cuentas/.

from django.contrib.auth import views as auth_views   # vistas de recuperación que trae Django
from django.urls import path, reverse_lazy            # reverse_lazy: resuelve la URL por nombre cuando hace falta

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

    # ---------------------------------------------------------------------
    # HU-03: Recuperación de contraseña
    # Se usan las vistas que ya trae Django; solo se les indica qué plantillas
    # y a qué ruta ir al terminar cada paso.
    # ---------------------------------------------------------------------

    # Paso 1 (CA-03.1): formulario donde el usuario escribe su correo.
    path('recuperar/', auth_views.PasswordResetView.as_view(
        template_name='cuentas/recuperar_form.html',
        email_template_name='cuentas/recuperar_correo.txt',
        subject_template_name='cuentas/recuperar_asunto.txt',
        success_url=reverse_lazy('cuentas:recuperar_enviado'),
    ), name='recuperar'),

    # Paso 2 (CA-03.2): mensaje genérico, exista o no el correo.
    path('recuperar/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='cuentas/recuperar_enviado.html',
    ), name='recuperar_enviado'),

    # Paso 3 (CA-03.5 y CA-03.6): enlace del correo; valida el token y pide la nueva contraseña.
    path('recuperar/confirmar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='cuentas/recuperar_confirmar.html',
        success_url=reverse_lazy('cuentas:recuperar_completo'),
    ), name='recuperar_confirmar'),

    # Paso 4: confirmación de que la contraseña fue cambiada.
    path('recuperar/completado/', auth_views.PasswordResetCompleteView.as_view(
        template_name='cuentas/recuperar_completo.html',
    ), name='recuperar_completo'),

    # ---------------------------------------------------------------------
    # HU-04: Cerrar sesión
    # LogoutView solo acepta POST (Django 5+ responde 405 a un GET), por eso el
    # botón de la plantilla es un <form method="post">. Al terminar, redirige
    # al inicio de sesión (CA-04.3).
    # ---------------------------------------------------------------------
    path('logout/', auth_views.LogoutView.as_view(
        next_page=reverse_lazy('cuentas:login'),
    ), name='logout'),
]