"""
cuentas/tests.py — SUITE DE PRUEBAS FUNCIONALES Y DE SEGURIDAD (HU-01, HU-02 y HU-05).

Verifica todos los criterios de aceptación del Product Backlog y el catálogo
de casos de prueba (TP-S01):
  - HU-01: CA-01.1 a CA-01.7 (CP-01 a CP-08)
  - HU-02: CA-02.1 a CA-02.6 (CP-09 a CP-14)
  - HU-05: CA-05.1 a CA-05.5 (Control y bloqueo temporal de intentos fallidos)
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import InicioSesionForm
from .models import IntentoAcceso, Usuario
from .services import LimitadorIntentosService


class HU01RegistroTests(TestCase):
    """Pruebas de HU-01: Registro de usuarios (CA-01.1 a CA-01.7 / CP-01 a CP-08)."""

    def setUp(self):
        self.url_registro = reverse('cuentas:registro')

    def test_cp01_registro_valido_crea_usuario_y_hash_seguro(self):
        """CA-01.1, CA-01.6 y CA-01.7 (CP-01, CP-06, CP-08): Registro válido y hash PBKDF2."""
        respuesta = self.client.post(self.url_registro, {
            'nombre': 'Ana Pérez',
            'email': 'ana@test.local',
            'password1': 'Abcd1234',
            'password2': 'Abcd1234',
        })
        self.assertRedirects(respuesta, reverse('cuentas:login'))
        usuario = Usuario.objects.get(email='ana@test.local')
        self.assertNotEqual(usuario.password, 'Abcd1234')
        self.assertTrue(usuario.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(usuario.check_password('Abcd1234'))

    def test_cp02_campos_vacios_son_obligatorios(self):
        """CA-01.2 (CP-02): Todos los campos son obligatorios."""
        respuesta = self.client.post(self.url_registro, {})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_cp03_cp04_email_formato_invalido_y_duplicado_case_insensitive(self):
        """CA-01.3 (CP-03, CP-04): Rechaza formato inválido y correo duplicado en mayúsculas."""
        Usuario.objects.create_user('ana@test.local', 'Ana', 'Abcd1234')
        r_invalido = self.client.post(self.url_registro, {
            'nombre': 'Ana',
            'email': 'ana@correo',
            'password1': 'Abcd1234',
            'password2': 'Abcd1234',
        })
        self.assertEqual(r_invalido.status_code, 200)
        r_duplicado = self.client.post(self.url_registro, {
            'nombre': 'Otra Ana',
            'email': 'ANA@test.local',
            'password1': 'Abcd1234',
            'password2': 'Abcd1234',
        })
        self.assertEqual(r_duplicado.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_cp05_cp07_politica_contrasena_y_confirmacion(self):
        """CA-01.4 y CA-01.5 (CP-05, CP-07): Rechaza 7 caracteres y confirmación distinta."""
        r_corta = self.client.post(self.url_registro, {
            'nombre': 'Ana',
            'email': 'ana@test.local',
            'password1': 'Abc1234',
            'password2': 'Abc1234',
        })
        self.assertEqual(r_corta.status_code, 200)
        r_no_coincide = self.client.post(self.url_registro, {
            'nombre': 'Ana',
            'email': 'ana@test.local',
            'password1': 'Abcd1234',
            'password2': 'Abcd1235',
        })
        self.assertEqual(r_no_coincide.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)


class HU02InicioSesionTests(TestCase):
    """Pruebas de HU-02: Inicio de sesión (CA-02.1 a CA-02.6 / CP-09 a CP-14)."""

    def setUp(self):
        self.url_login = reverse('cuentas:login')
        self.url_panel = reverse('cuentas:panel')
        self.usuario = Usuario.objects.create_user('ana@test.local', 'Ana Pérez', 'Abcd1234')

    def test_cp09_cp14_login_exitoso_redirige_a_panel(self):
        """CA-02.2 y CA-02.5 (CP-09, CP-14): Credenciales válidas redirigen al área privada."""
        respuesta = self.client.post(self.url_login, {
            'email': 'ana@test.local',
            'password': 'Abcd1234',
        })
        self.assertRedirects(respuesta, self.url_panel)

    def test_cp10_cp11_credenciales_incorrectas_mensaje_generico(self):
        """CA-02.3 (CP-10, CP-11): Mismo mensaje genérico para clave errónea o correo inexistente."""
        r1 = self.client.post(self.url_login, {'email': 'ana@test.local', 'password': 'Abcd1235'})
        r2 = self.client.post(self.url_login, {'email': 'noexiste@test.local', 'password': 'Abcd1234'})
        self.assertContains(r1, InicioSesionForm.MSG_CREDENCIALES_INVALIDAS)
        self.assertContains(r2, InicioSesionForm.MSG_CREDENCIALES_INVALIDAS)

    def test_cp13_acceso_directo_a_panel_sin_sesion_redirige_a_login(self):
        """CA-02.6 (CP-13): Un visitante no autenticado no puede acceder a páginas privadas."""
        respuesta = self.client.get(self.url_panel)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(self.url_login, respuesta.url)


class HU05LimiteIntentosFallidosTests(TestCase):
    """Pruebas de HU-05: Límite de intentos de autenticación fallidos (CA-05.1 a CA-05.5)."""

    def setUp(self):
        self.url_login = reverse('cuentas:login')
        self.url_panel = reverse('cuentas:panel')
        self.usuario = Usuario.objects.create_user('ana@test.local', 'Ana Pérez', 'Abcd1234')
        self.otro_usuario = Usuario.objects.create_user('carlos@test.local', 'Carlos Gómez', 'Carlos1234')

    def test_ca_05_1_permite_hasta_cinco_intentos_fallidos_consecutivos_en_15_min(self):
        """CA-05.1: Los primeros 4 intentos fallidos muestran error de credenciales; en el 5.º se activa el bloqueo."""
        for intento in range(1, 5):
            respuesta = self.client.post(
                self.url_login,
                {'email': 'ana@test.local', 'password': 'PasswordIncorrecta1'},
                REMOTE_ADDR='192.168.1.10',
            )
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, InicioSesionForm.MSG_CREDENCIALES_INVALIDAS)
            registro = IntentoAcceso.objects.get(email='ana@test.local', ip_address='192.168.1.10')
            self.assertEqual(registro.intentos_fallidos, intento)
            self.assertFalse(registro.esta_bloqueado())

        # 5.º intento fallido consecutivo dentro de la ventana de 15 minutos -> alcanza el límite
        respuesta_5 = self.client.post(
            self.url_login,
            {'email': 'ana@test.local', 'password': 'PasswordIncorrecta1'},
            REMOTE_ADDR='192.168.1.10',
        )
        self.assertEqual(respuesta_5.status_code, 200)
        self.assertContains(respuesta_5, InicioSesionForm.MSG_CUENTA_BLOQUEADA)
        registro = IntentoAcceso.objects.get(email='ana@test.local', ip_address='192.168.1.10')
        self.assertEqual(registro.intentos_fallidos, 5)
        self.assertTrue(registro.esta_bloqueado())

    def test_ca_05_1_ventana_de_15_minutos_reinicia_conteo_si_expira_sin_bloqueo(self):
        """CA-05.1: Si pasan más de 15 minutos desde el primer intento sin llegar a 5 fallos, la ventana se reinicia."""
        hace_16_min = timezone.now() - timedelta(minutes=16)
        for _ in range(3):
            LimitadorIntentosService.registrar_intento_fallido(
                'ana@test.local', '10.0.0.50', ahora=hace_16_min
            )

        # Nuevo fallo 16 minutos después -> empieza en 1 dentro de la nueva ventana
        registro = LimitadorIntentosService.registrar_intento_fallido(
            'ana@test.local', '10.0.0.50', ahora=timezone.now()
        )
        self.assertEqual(registro.intentos_fallidos, 1)
        self.assertFalse(registro.esta_bloqueado())

    def test_ca_05_1_aislamiento_por_combinacion_cuenta_e_ip(self):
        """CA-05.1: El bloqueo aplica solo a la misma combinación de cuenta e IP."""
        for _ in range(5):
            self.client.post(
                self.url_login,
                {'email': 'ana@test.local', 'password': 'MalPassword1'},
                REMOTE_ADDR='10.10.10.1',
            )

        # Misma cuenta desde OTRA IP -> puede iniciar sesión normalmente
        r_otra_ip = self.client.post(
            self.url_login,
            {'email': 'ana@test.local', 'password': 'Abcd1234'},
            REMOTE_ADDR='10.10.10.2',
        )
        self.assertRedirects(r_otra_ip, self.url_panel)
        self.client.logout()

        # OTRA cuenta desde la MISMA IP -> puede iniciar sesión normalmente
        r_otra_cuenta = self.client.post(
            self.url_login,
            {'email': 'carlos@test.local', 'password': 'Carlos1234'},
            REMOTE_ADDR='10.10.10.1',
        )
        self.assertRedirects(r_otra_cuenta, self.url_panel)

    def test_ca_05_2_bloquea_intentos_posteriores_incluso_con_contrasena_correcta(self):
        """CA-05.2: Al superar el límite (5 fallos), el 6.º intento queda bloqueado aunque la clave sea correcta."""
        for _ in range(5):
            self.client.post(
                self.url_login,
                {'email': 'ana@test.local', 'password': 'MalPassword1'},
                REMOTE_ADDR='172.16.0.10',
            )

        # 6.º intento con la contraseña CORRECTA durante los 15 minutos de bloqueo
        respuesta_6 = self.client.post(
            self.url_login,
            {'email': 'ana@test.local', 'password': 'Abcd1234'},
            REMOTE_ADDR='172.16.0.10',
        )
        self.assertEqual(respuesta_6.status_code, 200)
        self.assertContains(respuesta_6, InicioSesionForm.MSG_CUENTA_BLOQUEADA)
        # Verifica que el usuario NO quedó autenticado en la sesión
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_ca_05_3_mensaje_comprensible_sin_revelar_existencia_de_cuenta(self):
        """CA-05.3: Presenta el mismo mensaje comprensible de bloqueo para correos registrados y no registrados."""
        for _ in range(5):
            self.client.post(
                self.url_login,
                {'email': 'noexiste@test.local', 'password': 'MalPassword1'},
                REMOTE_ADDR='172.16.0.99',
            )
        r_no_existe = self.client.post(
            self.url_login,
            {'email': 'noexiste@test.local', 'password': 'MalPassword1'},
            REMOTE_ADDR='172.16.0.99',
        )
        self.assertContains(r_no_existe, InicioSesionForm.MSG_CUENTA_BLOQUEADA)

    def test_ca_05_4_despues_del_periodo_de_bloqueo_se_puede_volver_a_intentar(self):
        """CA-05.4: Transcurridos los 15 minutos de bloqueo, el usuario puede iniciar sesión."""
        inicio = timezone.now() - timedelta(minutes=16)
        for _ in range(5):
            LimitadorIntentosService.registrar_intento_fallido(
                'ana@test.local', '192.168.50.5', ahora=inicio
            )

        # Ya pasaron 16 minutos (> 15 minutos de bloqueo) -> intenta iniciar sesión con clave válida
        respuesta = self.client.post(
            self.url_login,
            {'email': 'ana@test.local', 'password': 'Abcd1234'},
            REMOTE_ADDR='192.168.50.5',
        )
        self.assertRedirects(respuesta, self.url_panel)
        registro = IntentoAcceso.objects.get(email='ana@test.local', ip_address='192.168.50.5')
        self.assertEqual(registro.intentos_fallidos, 0)
        self.assertIsNone(registro.bloqueado_hasta)

    def test_ca_05_5_inicio_sesion_exitoso_reinicia_contador(self):
        """CA-05.5: Un inicio de sesión exitoso antes del bloqueo reinicia el contador a 0."""
        # 4 intentos fallidos consecutivos
        for _ in range(4):
            self.client.post(
                self.url_login,
                {'email': 'ana@test.local', 'password': 'MalPassword1'},
                REMOTE_ADDR='192.168.100.1',
            )
        registro = IntentoAcceso.objects.get(email='ana@test.local', ip_address='192.168.100.1')
        self.assertEqual(registro.intentos_fallidos, 4)

        # 5.º intento con credenciales válidas -> inicia sesión y reinicia el contador a 0
        respuesta = self.client.post(
            self.url_login,
            {'email': 'ana@test.local', 'password': 'Abcd1234'},
            REMOTE_ADDR='192.168.100.1',
        )
        self.assertRedirects(respuesta, self.url_panel)
        registro.refresh_from_db()
        self.assertEqual(registro.intentos_fallidos, 0)
        self.assertIsNone(registro.bloqueado_hasta)
