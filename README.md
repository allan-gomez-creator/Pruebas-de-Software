# Pruebas de Software — Módulo de Autenticación (HU-01, HU-02 y HU-05)

Repositorio unificado que integra la configuración de base de datos de la rama `master` con el backend de autenticación de `feature/hu01-hu02-autenticacion` e implementa la **Historia de Usuario 5 (HU-05: Límite de intentos de autenticación fallidos)**.

---

En el archivo settings.py, en el apartado de DATABASE tienen que cambiar la PASSWORD por su contraseña del usuario postgres
Configuración del correo (HU-03: recuperar contraseña)

El proyecto tiene dos modos de envío de correo. Se elige solo, según si existen las variables de entorno EMAIL_HOST_USER y EMAIL_HOST_PASSWORD. Nadie debe escribir contraseñas dentro del código ni subirlas a Git.

Modo A: sin configurar nada (recomendado para desarrollar)

Si no defines las variables, el correo se imprime en la terminal donde corre el servidor.

Abre una terminal (CMD) en la carpeta del proyecto, donde está manage.py.
Ejecuta:
   python manage.py runserver
Abre http://127.0.0.1:8000/cuentas/recuperar/ y escribe el correo de un usuario registrado y activo.
En la terminal aparecerá el correo con el enlace de recuperación en una sola línea. Cópialo completo y pégalo en el navegador.
Modo B: envío real a la bandeja de entrada (Gmail)
Paso 1. Crear tu propia contraseña de aplicación

Cada persona crea la suya con su cuenta de Google. No se comparte la de otra persona.

Entra a tu cuenta de Google y activa la verificación en dos pasos.
Abre https://myaccount.google.com/apppasswords.
Escribe un nombre (por ejemplo Django Sprint1) y pulsa Crear.
Copia las 16 letras que aparecen, sin espacios. Solo se muestran una vez.
Paso 2. Definir las variables y arrancar el servidor

En CMD, dentro de la carpeta del proyecto, y en la misma ventana donde correrá el servidor:

set EMAIL_HOST_USER=tucorreo@gmail.com
set EMAIL_HOST_PASSWORD=LAS16LETRAS
python manage.py runserver

Estas variables duran solo mientras esa ventana siga abierta. Si la cierras, hay que repetirlas.

Paso 3. Probar
Abre http://127.0.0.1:8000/cuentas/recuperar/.
Escribe el correo de un usuario registrado y activo del sistema (puede ser el mismo tucorreo@gmail.com si te registraste con él).
Revisa la bandeja de entrada y la carpeta de spam. El asunto es “Recupera el acceso a tu cuenta”.
Abre el enlace, define una contraseña nueva y verifica que el mismo enlace ya no funciona.
Para no repetir los comandos (opcional)

Crea un archivo iniciar.bat con este contenido:

@echo off
set EMAIL_HOST_USER=tucorreo@gmail.com
set EMAIL_HOST_PASSWORD=LAS16LETRAS
python manage.py runserver

Agrégalo al .gitignore para que la contraseña nunca llegue al repositorio:

iniciar.bat
Cómo saber si falló

Django muestra “Revisa tu correo” aunque el envío falle (así lo exige CA-03.2). Siempre mira la terminal del servidor: si hay error, aparece Failed to send password reset email con la causa debajo.

Mensaje en la terminal	Causa y solución
SMTPAuthenticationError 535	Contraseña de aplicación mal copiada o revocada. Crea otra
Application-specific password required	Falta activar la verificación en dos pasos
SMTPServerDisconnected o STARTTLS extension not supported	Tu red o antivirus bloquea el SMTP. Prueba con datos del celular, desactiva el escudo de correo del antivirus o apaga la VPN. Si no se resuelve, usa el Modo A
ModuleNotFoundError: cuentas.correo_consola	Falta el archivo cuentas/correo_consola.py (haz git pull)
No hay error y no llega nada	Revisa spam, y que el correo escrito sea exactamente el de un usuario activo
Reglas de seguridad
Nunca escribas la contraseña de aplicación en settings.py, en el chat ni en capturas.
Nunca subas iniciar.bat ni archivos con contraseñas a Git.
Si una contraseña se expone, revócala en https://myaccount.google.com/apppasswords y crea otra.
Gmail sirve para pruebas y proyectos de clase (límite aproximado de 500 correos al día). En producción se usa un servicio transaccional como Brevo, SendGrid o Amazon SES.
## 1. Montar base de datos local (PostgreSQL — Rama `master`)

1. Ejecutar en la carpeta del proyecto:
   ```bash
   pip install django "psycopg[binary]"
   ```
2. Autenticarse en `psql`.
3. Ejecutar los siguientes comandos en la consola de Postgres en orden:
   ```sql
   CREATE DATABASE pruebas;
   \connect pruebas
   ```
4. Definir las variables de entorno para conectar con PostgreSQL (o ajustar `DB_PASSWORD` en `Sprint_1/settings.py`):
   ```powershell
   $env:DB_ENGINE="postgresql"
   $env:DB_NAME="pruebas"
   $env:DB_USER="postgres"
   $env:DB_PASSWORD="TU_PASSWORD"
   ```
   *(Por defecto, si no se define `DB_ENGINE`, el sistema utiliza `sqlite3` con `db.sqlite3` para facilitar el desarrollo y las pruebas locales).*
5. Ejecutar las migraciones:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

---

## 2. Ejecución del servidor y pruebas

- **Iniciar servidor de desarrollo:**
  ```bash
  python manage.py runserver
  ```
  - Registro (`HU-01`): `http://127.0.0.1:8000/cuentas/registro/`
  - Inicio de sesión y control de intentos (`HU-02` y `HU-05`): `http://127.0.0.1:8000/cuentas/login/`
  - Área privada (`HU-02`): `http://127.0.0.1:8000/cuentas/panel/`
  - Panel de administración (evidencia de tablas `Usuario` e `IntentoAcceso`): `http://127.0.0.1:8000/admin/`

- **Ejecutar suite de pruebas automatizadas (`HU-01`, `HU-02` y `HU-05`):**
  ```bash
  python manage.py test -v 2
  ```
