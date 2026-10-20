Montar base de datos local

1- Ejecutar pip install django "psycopg[binary]" en la carpeta "pruebas-de-software"
2- Autenticarse en psql
3- Ejecutar los siguientes comando en la consola de postgres en orden
3.1- CREATE DATABASE pruebas;
3.2- \connect pruebas
4- Ejecutar las migraciones con:
4.1- python manage.py makemigrations
4.2- python manage.py migrate 

-----IMPORTANTE-----

En el archivo settings.py, en el apartado de DATABASE tienen que cambiar la PASSWORD por su contraseña del usuario postgres
