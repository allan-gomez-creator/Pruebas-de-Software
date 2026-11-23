import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from cuentas.correo_consola import EmailBackend
from cuentas.models import IntentoAcceso
from cuentas.services import LimitadorIntentosService as Servicio
from despliegue import views as vistas_despliegue

Usuario = get_user_model()
CLAVE = "Prueba2026Ok"


class ObtenerIpTests(TestCase):
    def test_sin_request_devuelve_localhost(self):
        self.assertEqual(Servicio.obtener_ip_cliente(None), "127.0.0.1")

    def test_x_forwarded_for_toma_la_primera_ip(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2")
        self.assertEqual(Servicio.obtener_ip_cliente(request), "10.0.0.1")

    def test_remote_addr(self):
        request = RequestFactory().get("/", REMOTE_ADDR="192.168.1.5")
        self.assertEqual(Servicio.obtener_ip_cliente(request), "192.168.1.5")


class VentanaExpiradaTests(TestCase):
    def test_ventana_vencida_sin_bloqueo_reinicia_contador(self):
        t0 = timezone.now()
        Servicio.registrar_intento_fallido("ana@test.local", "1.1.1.1", ahora=t0)
        despues = t0 + timedelta(minutes=16)
        self.assertFalse(Servicio.esta_bloqueado("ana@test.local", "1.1.1.1", ahora=despues))
        registro = Servicio.obtener_registro("ana@test.local", "1.1.1.1")
        self.assertEqual(registro.intentos_fallidos, 0)


class IntentoAccesoStrTests(TestCase):
    def test_str_con_fallos(self):
        registro = Servicio.registrar_intento_fallido("ana@test.local", "1.1.1.1")
        self.assertIn("1 fallos", str(registro))

    def test_str_bloqueado(self):
        for _ in range(Servicio.max_intentos()):
            registro = Servicio.registrar_intento_fallido("ana@test.local", "1.1.1.1")
        self.assertIn("BLOQUEADO", str(registro))


class LoginNextInternoTests(TestCase):
    def test_next_interno_redirige_a_esa_pagina(self):
        Usuario.objects.create_user(email="ana@test.local", nombre="Ana", password=CLAVE)
        panel = reverse("cuentas:panel")
        r = self.client.post(
            reverse("cuentas:login"),
            {"email": "ana@test.local", "password": CLAVE, "next": panel},
        )
        self.assertRedirects(r, panel)


class CorreoConsolaTests(TestCase):
    def test_write_message_imprime_asunto_destinatario_y_cuerpo(self):
        salida = io.StringIO()
        backend = EmailBackend(stream=salida)
        mensaje = EmailMessage("Hola", "Cuerpo del correo", "origen@test.local", ["dest@test.local"])
        backend.write_message(mensaje)
        texto = salida.getvalue()
        self.assertIn("Asunto: Hola", texto)
        self.assertIn("Para: dest@test.local", texto)
        self.assertIn("Cuerpo del correo", texto)


class DespliegueViewsTests(TestCase):
    def test_hello(self):
        r = vistas_despliegue.hello(RequestFactory().get("/"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Hola Mundo", r.content)

    def test_about(self):
        r = vistas_despliegue.about(RequestFactory().get("/"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Acerca de", r.content)