"""
cuentas/views.py — VISTAS (los "controladores") de HU-01 y HU-02.

Una vista es una función que recibe la petición del navegador (request) y
devuelve una respuesta: una página HTML (render) o una redirección (redirect).

Las vistas con formulario siguen el mismo patrón:
    GET  -> el usuario abre la página: se muestra el formulario vacío.
    POST -> el usuario envió el formulario: se valida.
            * Válido   -> se ejecuta la acción y se REDIRIGE (patrón
                          Post/Redirect/Get: así recargar la página no
                          reenvía el formulario).
            * Inválido -> se vuelve a mostrar el formulario con los errores.
"""

from django.contrib import messages                          # mensajes de una sola vez ("¡Cuenta creada!")
from django.contrib.auth import login                        # crea la sesión del usuario
from django.contrib.auth.decorators import login_required    # exige sesión iniciada
from django.db import IntegrityError, transaction            # errores de BD y transacciones
from django.shortcuts import redirect, render                # responder con redirección o con HTML
from django.utils.http import url_has_allowed_host_and_scheme  # revisa que una URL sea de este sitio
from django.views.decorators.cache import never_cache        # prohíbe guardar la página en caché
from django.views.decorators.csrf import csrf_protect        # exige el token CSRF en los POST
from django.views.decorators.http import require_http_methods  # limita los métodos HTTP permitidos

from .forms import InicioSesionForm, RegistroForm


# Los decoradores (@...) envuelven la función y agregan comportamiento.
@csrf_protect                            # rechaza POST sin token CSRF (protección contra ataques CSRF)
@require_http_methods(['GET', 'POST'])   # cualquier otro método (PUT, DELETE...) recibe error 405
def registro(request):
    """HU-01 — Crear una cuenta.  URL: /cuentas/registro/"""

    # Si ya inició sesión, no tiene sentido registrarse: va a su panel.
    if request.user.is_authenticated:
        return redirect('cuentas:panel')

    # request.POST tiene los datos enviados. En un GET está vacío, y
    # "request.POST or None" da None: el formulario queda vacío y sin errores.
    form = RegistroForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            # transaction.atomic(): si algo falla al guardar, se deshace
            # todo y la base de datos queda como estaba.
            with transaction.atomic():
                usuario = form.save()
        except IntegrityError:
            # Caso raro: dos personas se registran con el mismo correo al
            # mismo tiempo. El formulario no lo alcanza a detectar, pero la
            # restricción UNIQUE de la base de datos sí, y lanza IntegrityError.
            form.add_error('email', 'Ya existe una cuenta registrada con este correo electrónico.')
        else:
            # "else" de un try = se ejecuta solo si NO hubo error.
            # CA-01.6: mensaje de confirmación. Se guarda en la sesión y se
            # muestra en la siguiente página que se abra (el login).
            messages.success(
                request,
                f'¡Cuenta creada con éxito, {usuario.get_short_name()}! Ya puedes iniciar sesión.',
            )
            # 'cuentas:login' = espacio de nombres "cuentas" + ruta llamada "login".
            return redirect('cuentas:login')

    # GET, o POST con errores: dibuja la plantilla pasándole el formulario.
    return render(request, 'cuentas/registro.html', {'form': form})


@csrf_protect
@never_cache                             # la página de login no se guarda en caché del navegador
@require_http_methods(['GET', 'POST'])
def iniciar_sesion(request):
    """HU-02 — Iniciar sesión con correo y contraseña.  URL: /cuentas/login/"""

    # Si ya tiene sesión, va directo a su panel.
    if request.user.is_authenticated:
        return redirect('cuentas:panel')

    # "next" es la página privada que el usuario intentó abrir antes de que
    # lo mandaran al login (ej. /cuentas/login/?next=/cuentas/panel/).
    # Llega en la URL (GET) o en un campo oculto del formulario (POST).
    siguiente = request.POST.get('next') or request.GET.get('next') or ''

    # El formulario de login recibe la petición porque authenticate() la usa.
    form = InicioSesionForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Credenciales correctas (CA-02.2). login() crea la sesión en el
        # servidor, envía la cookie de sesión al navegador y cambia el
        # identificador de sesión (protege contra "fijación de sesión").
        login(request, form.get_user())

        # CA-02.5: redirigir a una página privada. Si había "next", se vuelve
        # ahí, PERO solo si es una URL de este mismo sitio. Así nadie puede
        # usar el login para mandar gente a una página maliciosa externa
        # (ataque "open redirect").
        if siguiente and url_has_allowed_host_and_scheme(
            siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(siguiente)
        return redirect('cuentas:panel')

    # GET, o credenciales incorrectas: se muestra el formulario (con el
    # mensaje genérico si falló) y se conserva "next" para el campo oculto.
    return render(request, 'cuentas/login.html', {'form': form, 'next': siguiente})


# Los decoradores se aplican de abajo hacia arriba: primero login_required
# revisa la sesión y después never_cache agrega la cabecera anti-caché.
@never_cache          # Cache-Control: no-store -> el botón "Atrás" no muestra una copia guardada
@login_required       # CA-02.6: sin sesión -> redirige a LOGIN_URL?next=/cuentas/panel/
def panel(request):
    """Área privada (destino de CA-02.5).  URL: /cuentas/panel/"""
    # No necesita pasar datos: la plantilla accede al usuario con {{ user }}.
    return render(request, 'cuentas/panel.html')