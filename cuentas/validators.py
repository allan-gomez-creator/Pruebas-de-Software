"""
VALIDADOR DE COMPLEJIDAD DE CONTRASEÑA (CA-01.4).

Regla del Product Owner: al menos 8 caracteres, una mayúscula, una minúscula
y un número.
  - Los 8 caracteres los revisa MinimumLengthValidator de Django
    (configurado en settings.py con min_length=8).
  - Este archivo revisa lo demás: mayúscula, minúscula y número.

Para Django, un "validador de contraseña" es cualquier clase que tenga los
métodos validate() y get_help_text(). Al registrarlo en
AUTH_PASSWORD_VALIDATORS (settings.py), Django lo ejecuta automáticamente
cada vez que se llama a validate_password(): en el registro (HU-01) y, más
adelante, al recuperar la contraseña (HU-03, CA-03.5).
"""

import re                                           # expresiones regulares (búsqueda de patrones en texto)

from django.core.exceptions import ValidationError  # el error que Django muestra en el formulario


class ComplejidadContrasenaValidator:
    # Lista de reglas. Cada regla es una tupla de 3 elementos:
    #   (patrón a buscar, código del error, mensaje para el usuario)
    # [A-Z] = cualquier letra mayúscula, [a-z] = minúscula, [0-9] = dígito.
    reglas = (
        (r'[A-Z]', 'sin_mayuscula', 'La contraseña debe contener al menos una letra mayúscula.'),
        (r'[a-z]', 'sin_minuscula', 'La contraseña debe contener al menos una letra minúscula.'),
        (r'[0-9]', 'sin_numero', 'La contraseña debe contener al menos un número.'),
    )

    def validate(self, password, user=None):
        """Revisa la contraseña. Si incumple alguna regla, lanza ValidationError."""
        # Recorre las reglas y crea un error por CADA patrón que NO aparezca.
        # re.search(patron, texto) devuelve None si no encuentra el patrón.
        # (password or '') evita un error si la contraseña llega como None.
        errores = [
            ValidationError(mensaje, code=codigo)
            for patron, codigo, mensaje in self.reglas
            if not re.search(patron, password or '')
        ]
        # Si hubo errores, se lanzan todos juntos: el usuario ve de una vez
        # todo lo que le falta, en vez de corregir uno por uno.
        if errores:
            raise ValidationError(errores)

    def get_help_text(self):
        """Texto de ayuda que Django puede mostrar junto al campo de contraseña."""
        return 'Debe contener al menos una letra mayúscula, una minúscula y un número.'