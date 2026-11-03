# Pruebas de Software — Módulo de Autenticación (HU-01, HU-02 y HU-05)

Repositorio unificado que integra la configuración de base de datos de la rama `master` con el backend de autenticación de `feature/hu01-hu02-autenticacion` e implementa la **Historia de Usuario 5 (HU-05: Límite de intentos de autenticación fallidos)**.

---

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
