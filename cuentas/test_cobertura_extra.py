from unittest.mock import patch

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()
CLAVE = "Prueba2026Ok"


def crear(email="ana@test.local", nombre="Ana Prueba", **extra):
    return Usuario.objects.create_user(email=email, nombre=nombre, password=CLAVE, **extra)


class ModeloExtraTests(TestCase):
    def test_create_user_sin_email(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(email="", nombre="Ana", password=CLAVE)

    def test_create_user_sin_nombre(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(email="a@test.local", nombre="", password=CLAVE)

    def test_create_superuser(self):
        u = Usuario.objects.create_superuser("admin@test.local", "Admin", CLAVE)
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_superuser)

    def test_create_superuser_con_flags_invalidos(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser("a@test.local", "A", CLAVE, is_staff=False)
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser("b@test.local", "B", CLAVE, is_superuser=False)

    def test_str_y_nombres(self):
        u = crear()
        self.assertIn("ana@test.local", str(u))
        self.assertEqual(u.get_full_name(), "Ana Prueba")
        self.assertEqual(u.get_short_name(), "Ana")

    def test_short_name_sin_nombre_usa_email(self):
        self.assertEqual(Usuario(email="x@test.local", nombre="").get_short_name(), "x@test.local")

    def test_existe_email_ignora_mayusculas(self):
        crear()
        self.assertTrue(Usuario.objects.existe_email("ANA@test.local"))
        self.assertFalse(Usuario.objects.existe_email("otro@test.local"))


class ValidadorExtraTests(TestCase):
    def test_sin_minuscula(self):
        with self.assertRaises(ValidationError):
            password_validation.validate_password("PRUEBA2026OK")

    def test_sin_numero(self):
        with self.assertRaises(ValidationError):
            password_validation.validate_password("PruebaSinNumero")

    def test_sin_mayuscula(self):
        with self.assertRaises(ValidationError):
            password_validation.validate_password("prueba2026ok")

    def test_textos_de_ayuda(self):
        self.assertTrue(password_validation.password_validators_help_texts())


class VistasExtraTests(TestCase):
    def test_registro_autenticado_va_al_panel(self):
        self.client.force_login(crear())
        self.assertRedirects(self.client.get(reverse("cuentas:registro")), reverse("cuentas:panel"))

    def test_registro_integrity_error_muestra_error_en_email(self):
        datos = {"nombre": "Ana Prueba", "email": "ana@test.local",
                 "password1": CLAVE, "password2": CLAVE}
        with patch("cuentas.views.RegistroForm.save", side_effect=IntegrityError):
            r = self.client.post(reverse("cuentas:registro"), datos)
        self.assertEqual(r.status_code, 200)
        self.assertIn("email", r.context["form"].errors)

    def test_login_autenticado_va_al_panel(self):
        self.client.force_login(crear())
        self.assertRedirects(self.client.get(reverse("cuentas:login")), reverse("cuentas:panel"))

    def test_panel_autenticado(self):
        self.client.force_login(crear())
        self.assertEqual(self.client.get(reverse("cuentas:panel")).status_code, 200)