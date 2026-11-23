from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import TareaForm
from .models import EstadoTarea, Tarea
from .views import _mes_anterior_y_siguiente

Usuario = get_user_model()
CLAVE = "Prueba2026Ok"
RAPIDO = override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])


def datos(**cambios):
    d = {"nombre": "Entregar informe", "descripcion": "Informe final",
         "fecha_inicio": "2026-11-20", "fecha_fin": "2026-11-25", "estado": "Pendiente"}
    d.update(cambios)
    return d


def crear_tarea(usuario, nombre="Tarea base", **extra):
    campos = dict(nombre=nombre, descripcion="Detalle", fecha_inicio=date(2026, 11, 20),
                  fecha_fin=date(2026, 11, 25), estado=EstadoTarea.PENDIENTE)
    campos.update(extra)
    return Tarea.objects.create(usuario=usuario, **campos)


# ------------------------------------------------------------ FORMULARIO
class TareaFormTests(TestCase):
    def test_valido_con_los_cinco_campos(self):  # CA-01
        self.assertTrue(TareaForm(datos()).is_valid())

    def test_descripcion_es_opcional(self):
        self.assertTrue(TareaForm(datos(descripcion="")).is_valid())

    def test_nombre_vacio(self):  # CA-02
        form = TareaForm(datos(nombre=""))
        self.assertFalse(form.is_valid())
        self.assertIn("El nombre es obligatorio.", form.errors["nombre"])

    def test_nombre_solo_espacios(self):
        self.assertFalse(TareaForm(datos(nombre="   ")).is_valid())

    def test_fechas_obligatorias(self):  # CA-02
        form = TareaForm(datos(fecha_inicio="", fecha_fin=""))
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_inicio", form.errors)
        self.assertIn("fecha_fin", form.errors)

    def test_fechas_invertidas(self):  # CA-02 y CA-11
        form = TareaForm(datos(fecha_inicio="2026-11-25", fecha_fin="2026-11-20"))
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_fin", form.errors)

    def test_misma_fecha_es_valida(self):
        self.assertTrue(TareaForm(datos(fecha_inicio="2026-11-20", fecha_fin="2026-11-20")).is_valid())

    def test_estado_no_permitido(self):  # CA-10
        form = TareaForm(datos(estado="Cancelada"))
        self.assertFalse(form.is_valid())
        self.assertIn("estado", form.errors)

    def test_estados_permitidos(self):  # CA-10
        for estado in ("Pendiente", "En progreso", "Completada"):
            self.assertTrue(TareaForm(datos(estado=estado)).is_valid(), estado)


# ----------------------------------------------------------------- VISTAS
@RAPIDO
class AccesoSinSesionTests(TestCase):
    def test_visitante_redirigido_al_login(self):  # CA-09
        tarea = crear_tarea(Usuario.objects.create_user("a@test.local", "Ana", CLAVE))
        urls = [reverse("tareas:lista"), reverse("tareas:calendario"),
                reverse("tareas:crear"),
                reverse("tareas:detalle", args=[tarea.pk]),
                reverse("tareas:editar", args=[tarea.pk]),
                reverse("tareas:eliminar", args=[tarea.pk])]
        for url in urls:
            r = self.client.get(url)
            self.assertRedirects(r, f"{reverse('cuentas:login')}?next={url}", msg_prefix=url)

    def test_visitante_no_puede_crear_editar_ni_eliminar(self):  # CA-09
        tarea = crear_tarea(Usuario.objects.create_user("a@test.local", "Ana", CLAVE))
        self.client.post(reverse("tareas:crear"), datos())
        self.client.post(reverse("tareas:editar", args=[tarea.pk]), datos(nombre="Hackeada"))
        self.client.post(reverse("tareas:eliminar", args=[tarea.pk]))
        self.assertEqual(Tarea.objects.count(), 1)
        tarea.refresh_from_db()
        self.assertEqual(tarea.nombre, "Tarea base")


@RAPIDO
class CrearTareaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("a@test.local", "Ana", CLAVE)
        self.client.force_login(self.usuario)
        self.url = reverse("tareas:crear")

    def test_get_muestra_formulario(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_crear_valida(self):  # CA-01
        r = self.client.post(self.url, datos())
        self.assertRedirects(r, reverse("tareas:lista"))
        tarea = Tarea.objects.get()
        self.assertEqual(tarea.usuario, self.usuario)
        self.assertEqual(tarea.estado, "Pendiente")

    def test_nombre_vacio_no_crea(self):  # CA-02
        r = self.client.post(self.url, datos(nombre=""))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Tarea.objects.count(), 0)

    def test_fechas_invertidas_no_crea(self):  # CA-02
        r = self.client.post(self.url, datos(fecha_inicio="2026-11-25", fecha_fin="2026-11-20"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Tarea.objects.count(), 0)

    def test_estado_no_permitido_no_crea(self):  # CA-10
        r = self.client.post(self.url, datos(estado="Cancelada"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Tarea.objects.count(), 0)

    def test_metodo_no_permitido(self):
        self.assertEqual(self.client.delete(self.url).status_code, 405)


@RAPIDO
class LeerTareasYCalendarioTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user("a@test.local", "Ana", CLAVE)
        self.luis = Usuario.objects.create_user("l@test.local", "Luis", CLAVE)
        self.client.force_login(self.ana)

    def test_listado_muestra_tarea_guardada(self):  # CA-03
        crear_tarea(self.ana, nombre="Estudiar Django")
        r = self.client.get(reverse("tareas:lista"))
        self.assertContains(r, "Estudiar Django")

    def test_tarea_aparece_en_listado_y_calendario_en_rango_de_fechas(self):  # CA-03
        tarea = crear_tarea(
            self.ana,
            nombre="Sprint Review",
            fecha_inicio=date(2026, 11, 20),
            fecha_fin=date(2026, 11, 22),
            estado=EstadoTarea.EN_PROGRESO,
        )
        for nombre_url in ("tareas:lista", "tareas:calendario"):
            r = self.client.get(reverse(nombre_url), {"anio": 2026, "mes": 11})
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, "Sprint Review")
            # Aparece en cada día dentro del rango 20..22 de noviembre
            for dia in ("2026-11-20", "2026-11-21", "2026-11-22"):
                self.assertContains(r, f'data-evento-fecha="{dia}"')
            # No aparece fuera del rango (19 ni 23 de noviembre)
            self.assertNotContains(r, 'data-evento-fecha="2026-11-19"')
            self.assertNotContains(r, 'data-evento-fecha="2026-11-23"')
            self.assertContains(r, f'data-tarea-id="{tarea.pk}"')

    def test_calendario_sin_tareas_usa_mes_actual_y_maneja_parametros_invalidos(self):
        r = self.client.get(reverse("tareas:calendario"), {"anio": "invalido", "mes": "99"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Calendario")

    def test_mes_anterior_y_siguiente_cambio_de_anio(self):
        self.assertEqual(_mes_anterior_y_siguiente(2026, 1), ((2025, 12), (2026, 2)))
        self.assertEqual(_mes_anterior_y_siguiente(2026, 12), ((2026, 11), (2027, 1)))

    def test_listado_solo_muestra_tareas_propias(self):
        crear_tarea(self.ana, nombre="De Ana")
        crear_tarea(self.luis, nombre="De Luis")
        r = self.client.get(reverse("tareas:lista"))
        self.assertContains(r, "De Ana")
        self.assertNotContains(r, "De Luis")

    def test_detalle_muestra_datos_completos(self):  # CA-04
        tarea = crear_tarea(self.ana, nombre="Con detalle", descripcion="Descripcion completa")
        r = self.client.get(reverse("tareas:detalle", args=[tarea.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Con detalle")
        self.assertContains(r, "Descripcion completa")

    def test_detalle_de_otro_usuario_da_404(self):
        ajena = crear_tarea(self.luis)
        self.assertEqual(self.client.get(reverse("tareas:detalle", args=[ajena.pk])).status_code, 404)

    def test_detalle_inexistente_da_404(self):  # CA-12
        self.assertEqual(self.client.get(reverse("tareas:detalle", args=[9999])).status_code, 404)


@RAPIDO
class EditarTareaTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user("a@test.local", "Ana", CLAVE)
        self.luis = Usuario.objects.create_user("l@test.local", "Luis", CLAVE)
        self.client.force_login(self.ana)
        self.tarea = crear_tarea(
            self.ana,
            nombre="Tarea original",
            descripcion="Descripcion inicial",
            fecha_inicio=date(2026, 11, 10),
            fecha_fin=date(2026, 11, 12),
            estado=EstadoTarea.PENDIENTE,
        )
        self.url = reverse("tareas:editar", args=[self.tarea.pk])

    def test_get_muestra_formulario_precargado(self):  # CA-05
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Editar tarea")
        self.assertContains(r, "Tarea original")
        self.assertContains(r, "Descripcion inicial")

    def test_modificar_nombre_descripcion_fechas_y_estado_se_refleja_en_listado_y_calendario(self):  # CA-05 y CA-06
        nuevos_datos = {
            "nombre": "Tarea actualizada",
            "descripcion": "Nueva descripcion detallada",
            "fecha_inicio": "2026-11-15",
            "fecha_fin": "2026-11-17",
            "estado": EstadoTarea.COMPLETADA,
        }
        r = self.client.post(self.url, nuevos_datos)
        self.assertRedirects(r, reverse("tareas:lista"))

        # CA-05: Verificar cambios persistidos en la base de datos
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.nombre, "Tarea actualizada")
        self.assertEqual(self.tarea.descripcion, "Nueva descripcion detallada")
        self.assertEqual(self.tarea.fecha_inicio, date(2026, 11, 15))
        self.assertEqual(self.tarea.fecha_fin, date(2026, 11, 17))
        self.assertEqual(self.tarea.estado, EstadoTarea.COMPLETADA)

        # CA-06: Los cambios guardados se reflejan en el listado y en el calendario
        r_lista = self.client.get(reverse("tareas:lista"), {"anio": 2026, "mes": 11})
        self.assertContains(r_lista, "Tarea actualizada")
        self.assertNotContains(r_lista, "Tarea original")
        self.assertContains(r_lista, "15/11/2026")
        self.assertContains(r_lista, "17/11/2026")
        self.assertContains(r_lista, "Completada")

        # En el calendario aparece ahora en el nuevo rango 15..17 y ya no en el antiguo 10..12
        for dia_nuevo in ("2026-11-15", "2026-11-16", "2026-11-17"):
            self.assertContains(r_lista, f'data-evento-fecha="{dia_nuevo}"')
        for dia_antiguo in ("2026-11-10", "2026-11-11", "2026-11-12"):
            self.assertNotContains(r_lista, f'data-evento-fecha="{dia_antiguo}"')

        r_cal = self.client.get(reverse("tareas:calendario"), {"anio": 2026, "mes": 11})
        self.assertContains(r_cal, "Tarea actualizada")
        for dia_nuevo in ("2026-11-15", "2026-11-16", "2026-11-17"):
            self.assertContains(r_cal, f'data-evento-fecha="{dia_nuevo}"')

    def test_editar_con_datos_invalidos_no_modifica(self):  # CA-02 y CA-05
        r = self.client.post(
            self.url,
            datos(nombre="", fecha_inicio="2026-11-25", fecha_fin="2026-11-20"),
        )
        self.assertEqual(r.status_code, 200)
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.nombre, "Tarea original")

    def test_no_puede_editar_tarea_de_otro_usuario(self):
        ajena = crear_tarea(self.luis, nombre="De Luis")
        r = self.client.post(reverse("tareas:editar", args=[ajena.pk]), datos(nombre="Intruso"))
        self.assertEqual(r.status_code, 404)
        ajena.refresh_from_db()
        self.assertEqual(ajena.nombre, "De Luis")

    def test_editar_inexistente_da_404(self):  # CA-12
        self.assertEqual(self.client.get(reverse("tareas:editar", args=[9999])).status_code, 404)
        self.assertEqual(self.client.post(reverse("tareas:editar", args=[9999]), datos()).status_code, 404)


@RAPIDO
class EliminarTareaTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user("a@test.local", "Ana", CLAVE)
        self.luis = Usuario.objects.create_user("l@test.local", "Luis", CLAVE)
        self.client.force_login(self.ana)

    def test_get_pide_confirmacion_y_no_borra(self):  # CA-07
        tarea = crear_tarea(self.ana)
        r = self.client.get(reverse("tareas:eliminar", args=[tarea.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Tarea.objects.filter(pk=tarea.pk).exists())

    def test_post_elimina_y_desaparece_del_listado(self):  # CA-07 y CA-08
        tarea = crear_tarea(self.ana, nombre="Para borrar")
        r = self.client.post(reverse("tareas:eliminar", args=[tarea.pk]))
        self.assertRedirects(r, reverse("tareas:lista"))
        self.assertFalse(Tarea.objects.filter(pk=tarea.pk).exists())
        self.assertNotContains(self.client.get(reverse("tareas:lista")), "Para borrar")

    def test_eliminar_inexistente_da_404(self):  # CA-12
        self.assertEqual(self.client.post(reverse("tareas:eliminar", args=[9999])).status_code, 404)

    def test_no_puede_eliminar_tarea_ajena(self):
        ajena = crear_tarea(self.luis)
        r = self.client.post(reverse("tareas:eliminar", args=[ajena.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertTrue(Tarea.objects.filter(pk=ajena.pk).exists())
