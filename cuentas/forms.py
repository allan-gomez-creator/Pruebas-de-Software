"""
cuentas/forms.py — FORMULARIOS: aquí vive la VALIDACIÓN de HU-01 y HU-02.

Un formulario de Django hace tres cosas:
  1. Define qué campos tiene (y con eso se dibuja el HTML).
  2. Recibe lo que escribió el usuario (request.POST).
  3. Valida los datos: form.is_valid() devuelve True o False y llena
     form.errors con los mensajes de cada campo.

Orden en que Django valida al llamar is_valid():
  a) Cada campo por separado (obligatorio, formato de correo, longitud...).
  b) Los métodos clean_<campo>() para reglas propias de un campo.
  c) El método clean() para reglas que comparan varios campos.

La validación se hace en el SERVIDOR porque la del navegador (HTML o
JavaScript) se puede saltar fácilmente.
"""

from django import forms
# authenticate: revisa correo + contraseña contra la base de datos.
# password_validation: ejecuta los validadores de AUTH_PASSWORD_VALIDATORS.
from django.contrib.auth import authenticate, password_validation

from .models import Usuario, normalizar_email

# Mensaje común para campos vacíos (CA-01.2 y CA-02.4).
MSG_OBLIGATORIO = 'Este campo es obligatorio.'


# =============================================================================
# HU-01 — Registro de usuarios
# =============================================================================
class RegistroForm(forms.Form):
    """Formulario de "Crear cuenta"."""

    # CA-01.1: el formulario pide nombre, correo, contraseña y confirmación.
    # CA-01.2: todos son obligatorios (required=True es el valor por defecto
    #          de cualquier campo, por eso no se escribe).

    # CharField = texto. Por defecto quita espacios de los extremos, así que
    # un nombre de solo espacios cuenta como vacío.
    nombre = forms.CharField(
        label='Nombre completo',                       # texto de la etiqueta <label>
        max_length=150,                                # igual que en el modelo
        error_messages={'required': MSG_OBLIGATORIO},  # mensaje si llega vacío
        # widget = cómo se dibuja en HTML. autocomplete ayuda al navegador a
        # sugerir datos; placeholder es el texto gris de ejemplo.
        widget=forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Ana Pérez'}),
    )

    # EmailField valida el FORMATO del correo (CA-01.3): rechaza 'ana@correo'
    # porque al dominio le falta el punto (.com, .local...).
    email = forms.EmailField(
        label='Correo electrónico',
        max_length=254,
        error_messages={
            'required': MSG_OBLIGATORIO,
            'invalid': 'Ingresa un correo electrónico con formato válido (ej. nombre@dominio.com).',
        },
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'nombre@dominio.com'}),
    )

    # strip=False: NO quitar espacios, porque un espacio también es parte de
    # una contraseña. PasswordInput dibuja <input type="password"> (puntos).
    password1 = forms.CharField(
        label='Contraseña',
        strip=False,
        error_messages={'required': MSG_OBLIGATORIO},
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Mínimo 8 caracteres, con al menos una mayúscula, una minúscula y un número.',
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        strip=False,
        error_messages={'required': MSG_OBLIGATORIO},
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def clean_email(self):
        """Regla propia del campo email: que no esté ya registrado (CA-01.3)."""
        # self.cleaned_data tiene los valores que ya pasaron la validación
        # básica. Se normaliza: ' ANA@Test.local ' -> 'ana@test.local'.
        email = normalizar_email(self.cleaned_data['email'])
        # Si ya existe (sin importar mayúsculas), se rechaza.
        if Usuario.objects.existe_email(email):
            raise forms.ValidationError(
                'Ya existe una cuenta registrada con este correo electrónico.',
                code='email_duplicado',
            )
        # Lo que se retorna es lo que queda guardado en cleaned_data['email'].
        return email

    def clean_password1(self):
        """Regla propia de password1: las reglas de seguridad (CA-01.4)."""
        password = self.cleaned_data['password1']
        # Ejecuta TODOS los validadores de settings.AUTH_PASSWORD_VALIDATORS
        # (longitud mínima 8 + nuestro ComplejidadContrasenaValidator).
        # Si alguno falla, lanza ValidationError y el mensaje sale bajo el campo.
        password_validation.validate_password(password)
        return password

    def clean(self):
        """Regla que compara dos campos: contraseña = confirmación (CA-01.5)."""
        cleaned = super().clean()                 # ejecuta primero la limpieza de la clase base
        # .get() devuelve None si el campo tuvo errores antes (por eso no se usa [ ]).
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        # Solo se comparan si ambas llegaron bien; si no, ya hay otro error.
        if p1 and p2 and p1 != p2:
            # add_error pone el mensaje debajo del campo "Confirmar contraseña".
            self.add_error('password2', forms.ValidationError(
                'Las contraseñas no coinciden.', code='password_no_coincide'))
        return cleaned

    def save(self) -> Usuario:
        """Crea el usuario en la base de datos (CA-01.6). Solo se llama si is_valid() fue True."""
        # create_user() aplica el hash a la contraseña (CA-01.7).
        return Usuario.objects.create_user(
            email=self.cleaned_data['email'],
            nombre=self.cleaned_data['nombre'],
            password=self.cleaned_data['password1'],
        )


# =============================================================================
# HU-02 — Inicio de sesión
# =============================================================================
class InicioSesionForm(forms.Form):
    """Formulario de "Iniciar sesión"."""

    # CA-02.3: UN SOLO mensaje para cualquier fallo de credenciales. No dice
    # si el correo no existe o si la contraseña está mal, para que nadie
    # pueda averiguar qué correos están registrados.
    MSG_CREDENCIALES_INVALIDAS = 'Correo electrónico o contraseña incorrectos.'

    # CA-02.1: pide correo y contraseña. CA-02.4: ambos obligatorios.
    # Aquí el correo es CharField y no EmailField a propósito: con EmailField,
    # un correo mal escrito daría un error distinto al mensaje genérico.
    email = forms.CharField(
        label='Correo electrónico',
        max_length=254,
        error_messages={'required': MSG_OBLIGATORIO},
        # autofocus: el cursor queda en este campo al abrir la página.
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'autofocus': True,
                                       'placeholder': 'nombre@dominio.com'}),
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        error_messages={'required': MSG_OBLIGATORIO},
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    def __init__(self, request=None, *args, **kwargs):
        """Constructor: guarda la petición porque authenticate() la necesita."""
        self.request = request
        self.usuario = None                       # aquí quedará el usuario si el login es correcto
        super().__init__(*args, **kwargs)         # inicializa el formulario normal de Django

    def clean(self):
        """Intenta autenticar con el correo y la contraseña escritos."""
        cleaned = super().clean()
        email, password = cleaned.get('email'), cleaned.get('password')

        # Si falta algún campo ya hay un error "obligatorio" y no se intenta
        # autenticar (CA-02.4).
        if email and password:
            # authenticate() busca al usuario por correo (get_by_natural_key)
            # y compara el HASH de la contraseña. Devuelve el usuario si todo
            # está bien, o None si:
            #   - el correo no existe,
            #   - la contraseña es incorrecta,
            #   - la cuenta está inactiva (is_active=False).
            # Si el correo no existe, igual calcula un hash para que el tiempo
            # de respuesta no delate qué correos están registrados.
            self.usuario = authenticate(self.request, email=normalizar_email(email), password=password)
            if self.usuario is None:
                # Error "general" del formulario (no de un campo): se muestra
                # arriba, en la caja roja. Siempre el mismo texto (CA-02.3).
                raise forms.ValidationError(self.MSG_CREDENCIALES_INVALIDAS, code='credenciales_invalidas')
        return cleaned

    def get_user(self):
        """Devuelve el usuario autenticado (lo usa la vista para hacer login())."""
        return self.usuario