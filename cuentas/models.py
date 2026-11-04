"""
MODELO DE DATOS del módulo de autenticación.

Un "modelo" es una clase de Python que Django convierte en una tabla de la
base de datos: cada atributo de la clase es una columna y cada objeto es una
fila. Aquí se define la tabla de usuarios.

¿Por qué un modelo propio? El usuario que trae Django inicia sesión con un
"username". HU-01 y HU-02 piden iniciar sesión con el CORREO, así que se crea
un usuario donde el correo es el identificador.
"""

# AbstractBaseUser: trae lo básico de un usuario (campo password con hash,
#                   last_login y métodos como set_password / check_password).
# BaseUserManager:  clase base para el "manager", el objeto que crea usuarios.
# PermissionsMixin: agrega is_superuser, grupos y permisos (necesario para /admin/).
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models                      # tipos de columnas (CharField, EmailField...)
from django.db.models.functions import Lower      # función SQL LOWER() para la restricción única
from django.utils import timezone                 # fecha y hora actual con zona horaria


def normalizar_email(email: str) -> str:
    """Deja el correo en una forma única: sin espacios y en minúsculas.

    Ejemplo: '  ANA@Test.local ' -> 'ana@test.local'.
    Así 'ANA@test.local' y 'ana@test.local' cuentan como el MISMO correo
    (CA-01.3: único sin distinguir mayúsculas de minúsculas).
    """
    # (email or '') evita un error si llega None; strip() quita espacios de
    # los extremos y lower() pasa todo a minúsculas.
    return (email or '').strip().lower()


class UsuarioManager(BaseUserManager):
    """El "manager" es lo que se usa como Usuario.objects.<algo>.

    Aquí se define CÓMO se crea un usuario normal y un superusuario, y cómo
    se busca un usuario al iniciar sesión.
    """

    # Permite que las migraciones también conozcan este manager.
    use_in_migrations = True

    def create_user(self, email, nombre, password=None, **extra_fields):
        """Crea y guarda un usuario normal. Lo usa el registro (HU-01)."""
        # Validaciones mínimas: sin correo o sin nombre no se puede crear.
        if not email:
            raise ValueError('El correo electrónico es obligatorio.')
        if not nombre:
            raise ValueError('El nombre es obligatorio.')

        # self.model es la clase Usuario. Se crea el objeto en memoria (aún no
        # está en la base de datos) con el correo normalizado y el nombre sin
        # espacios sobrantes.
        usuario = self.model(email=normalizar_email(email), nombre=nombre.strip(), **extra_fields)

        # set_password() NO guarda la contraseña: calcula su HASH (PBKDF2-SHA256
        # con sal aleatoria) y guarda ese hash. Esto cumple CA-01.7.
        usuario.set_password(password)

        # Ahora sí se inserta la fila en la base de datos.
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, nombre, password=None, **extra_fields):
        """Crea un administrador. Lo usa `python manage.py createsuperuser`."""
        # setdefault: si no vienen estos valores, se ponen en True.
        extra_fields.setdefault('is_staff', True)        # puede entrar a /admin/
        extra_fields.setdefault('is_superuser', True)    # tiene todos los permisos
        if not extra_fields['is_staff'] or not extra_fields['is_superuser']:
            raise ValueError('Un superusuario debe tener is_staff=True e is_superuser=True.')
        # Reutiliza create_user para no repetir la lógica del hash.
        return self.create_user(email, nombre, password, **extra_fields)

    def get_by_natural_key(self, email):
        """Busca al usuario por su correo. Django lo llama al iniciar sesión.

        email__iexact significa "igual, ignorando mayúsculas" (en SQL:
        WHERE LOWER(email) = LOWER(...)). Por eso 'ANA@test.local' también
        puede iniciar sesión (HU-02).
        """
        return self.get(email__iexact=normalizar_email(email))

    def existe_email(self, email) -> bool:
        """Devuelve True si ya hay una cuenta con ese correo (sin importar mayúsculas)."""
        # .exists() hace una consulta muy liviana: solo pregunta si hay filas.
        return self.filter(email__iexact=normalizar_email(email)).exists()


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Tabla cuentas_usuario: una fila por cada persona registrada."""

    # ---------- Columnas de la tabla ----------
    # El primer texto de cada campo es el nombre que se muestra en el admin.
    nombre = models.CharField('nombre', max_length=150)                          # varchar(150)
    email = models.EmailField('correo electrónico', max_length=254, unique=True)  # varchar(254) UNIQUE
    is_active = models.BooleanField('activo', default=True)        # una cuenta inactiva no puede iniciar sesión
    is_staff = models.BooleanField('acceso al administrador', default=False)  # puede entrar a /admin/
    fecha_registro = models.DateTimeField('fecha de registro', default=timezone.now)  # se llena sola al crear
    # Heredados de las clases base (no hay que escribirlos):
    #   password     -> guarda el HASH, nunca la contraseña real
    #   last_login   -> fecha del último inicio de sesión
    #   is_superuser -> todos los permisos

    # Conecta el manager de arriba: Usuario.objects.create_user(...)
    objects = UsuarioManager()

    # ---------- Configuración para el sistema de autenticación ----------
    USERNAME_FIELD = 'email'          # el campo con el que se inicia sesión
    EMAIL_FIELD = 'email'             # el campo de correo (lo usará HU-03 para recuperar contraseña)
    REQUIRED_FIELDS = ['nombre']      # datos extra que pide `createsuperuser` además del correo

    class Meta:
        # Nombres que se muestran en el admin.
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        # Orden por defecto en las consultas: los más recientes primero.
        ordering = ['-fecha_registro']
        constraints = [
            # Índice único sobre LOWER(email): la BASE DE DATOS rechaza
            # 'ANA@test.local' si ya existe 'ana@test.local' (CA-01.3).
            # Es una segunda capa de seguridad, por si alguien crea usuarios
            # sin pasar por el formulario (admin, scripts, etc.).
            models.UniqueConstraint(Lower('email'), name='usuario_email_unico_ci'),
        ]

    def save(self, *args, **kwargs):
        """Se ejecuta cada vez que se guarda un usuario."""
        # Antes de guardar, normaliza el correo, venga de donde venga.
        self.email = normalizar_email(self.email)
        # super().save() llama al save original de Django, que hace el INSERT/UPDATE.
        super().save(*args, **kwargs)

    def __str__(self):
        """Texto que representa al usuario (se ve en el admin y en la consola)."""
        return f'{self.nombre} <{self.email}>'

    def get_full_name(self):
        """Nombre completo. Django lo usa en algunas pantallas."""
        return self.nombre

    def get_short_name(self):
        """Primer nombre: 'Ana Prueba' -> 'Ana'. Se usa en el saludo y la barra."""
        return self.nombre.split(' ')[0] if self.nombre else self.email