# cuentas/middleware.py — Evita que el navegador guarde páginas de usuarios autenticados.
from django.utils.cache import add_never_cache_headers


class SinCachePrivadasMiddleware:
    """Agrega 'Cache-Control: no-store' a toda respuesta dada a un usuario autenticado.

    Así, al cerrar sesión y pulsar Atrás, el navegador debe volver a pedir la página
    al servidor, y como ya no hay sesión, lo manda al inicio de sesión (CA-04.4).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            add_never_cache_headers(response)
        return response