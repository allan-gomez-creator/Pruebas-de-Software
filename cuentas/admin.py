# cuentas/admin.py — PANEL DE ADMINISTRACIÓN (/admin/).
# Le dice al admin de Django cómo mostrar y editar el modelo Usuario.
# El admin trae una pantalla de usuarios pensada para "username"; aquí se
# adapta a nuestro usuario con correo y nombre.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin            # pantalla de usuarios que trae Django
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm  # formularios base del admin

from .models import Usuario                                # nuestro modelo (el punto = "de esta misma app")


class UsuarioCreationForm(AdminUserCreationForm):
    """Formulario de "Añadir usuario" en el admin."""
    class Meta:
        model = Usuario                 # usa nuestro modelo en lugar del User de Django
        fields = ('email', 'nombre')    # campos que pide (las contraseñas las agrega la clase base)


class UsuarioChangeForm(UserChangeForm):
    """Formulario de "Modificar usuario" en el admin."""
    class Meta:
        model = Usuario
        fields = '__all__'              # todos los campos del modelo


# @admin.register(Usuario) registra el modelo en el admin con esta configuración.
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    add_form = UsuarioCreationForm      # formulario para crear
    form = UsuarioChangeForm            # formulario para editar

    # Columnas de la lista de usuarios.
    list_display = ('email', 'nombre', 'is_active', 'is_staff', 'fecha_registro', 'last_login')
    # Filtros de la barra lateral derecha.
    list_filter = ('is_active', 'is_staff')
    # Campos en los que busca la caja de búsqueda.
    search_fields = ('email', 'nombre')
    # Orden de la lista: más recientes primero.
    ordering = ('-fecha_registro',)
    # Campos que se ven pero no se pueden editar.
    readonly_fields = ('fecha_registro', 'last_login')

    # Secciones de la pantalla "Modificar usuario". El campo password se
    # muestra como hash (algoritmo, iteraciones, sal): sirve como evidencia de CP-08.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Datos personales', {'fields': ('nombre',)}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('fecha_registro', 'last_login')}),
    )
    # Campos de la pantalla "Añadir usuario".
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2'),
        }),
    )