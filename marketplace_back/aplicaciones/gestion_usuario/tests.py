import re
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from aplicaciones.validacion import (
    normalizar_espacios, validar_fecha_no_futura, validar_solo_digitos,
    validar_solo_letras, validar_usuario,
)
from .autenticacion import AutenticacionCorreoOUsuario
from .models import Auditoria, Usuario
from .validacion import ValidacionComplejidadContrasena

CLAVE = 'Clave#Segura2026'


def crear_usuario(nombre='huesped1', correo='huesped1@correo.com', rol=Usuario.ROL_HUESPED,
                  verificado=True, **extra):
    usuario = Usuario.objects.create_user(
        username=nombre, email=correo, password=CLAVE,
        first_name='Ana', last_name='Pérez', correo_verificado=verificado, **extra)
    usuario.groups.add(Group.objects.get(name=rol))
    return usuario


def datos_registro(**cambios):
    datos = {
        'nombre_usuario': 'nuevo.usuario', 'nombres': 'María José', 'apellidos': 'Gómez',
        'correo': 'Nuevo@Correo.com', 'telefono': '3001234567', 'rol': 'Huesped',
        'contrasena': CLAVE, 'confirmar_contrasena': CLAVE,
    }
    datos.update(cambios)
    return datos


class BaseApi(TestCase):
    def setUp(self):
        self.cliente = APIClient()

    def ultima_auditoria(self, accion):
        return Auditoria.objects.filter(accion=accion).order_by('-id').first()


class ValidacionTests(TestCase):
    def test_contrasena_compleja_valida(self):
        ValidacionComplejidadContrasena().validate(CLAVE)

    def test_contrasena_incumple_cada_regla(self):
        casos = {
            'Ab#1': 'longitud_invalida', 'clave#segura1': 'sin_mayuscula',
            'CLAVE#SEGURA1': 'sin_minuscula', 'Clave#Segura': 'sin_numero',
            'ClaveSegura12': 'sin_simbolo', 'A' * 60 + 'b#1' + 'x' * 5: 'longitud_invalida',
        }
        for clave, codigo in casos.items():
            with self.subTest(clave=clave):
                with self.assertRaises(ValidationError) as error:
                    ValidacionComplejidadContrasena().validate(clave)
                self.assertEqual(error.exception.code, codigo)

    def test_validaciones_compartidas(self):
        validar_solo_letras('José Ñuñez')
        validar_usuario('ana.perez_01')
        validar_solo_digitos('300123')
        self.assertEqual(normalizar_espacios('  Ana   María '), 'Ana María')
        for funcion, valor in [(validar_solo_letras, 'Ana3'), (validar_usuario, 'ana perez'),
                               (validar_solo_digitos, '30a'),
                               (validar_fecha_no_futura, timezone.localdate() + timedelta(days=1))]:
            with self.subTest(funcion=funcion.__name__):
                with self.assertRaises(ValidationError):
                    funcion(valor)


class RegistroTests(BaseApi):
    url = reverse('registro')

    def test_registro_exitoso(self):
        respuesta = self.cliente.post(self.url, datos_registro(), format='json')
        self.assertEqual(respuesta.status_code, 201)
        usuario = Usuario.objects.get(username='nuevo.usuario')
        self.assertEqual(usuario.email, 'nuevo@correo.com')
        self.assertEqual(usuario.estado, Usuario.Estado.ACTIVO)
        self.assertFalse(usuario.correo_verificado)
        self.assertTrue(usuario.es_huesped())
        self.assertNotEqual(usuario.password, CLAVE)
        self.assertTrue(usuario.check_password(CLAVE))
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(re.search(r'\d{6}', mail.outbox[0].body).group(), usuario.codigo_verificacion)
        registro = self.ultima_auditoria(Auditoria.Accion.REGISTRO)
        self.assertEqual(registro.usuario, usuario)
        self.assertEqual(registro.resultado, Auditoria.Resultado.EXITOSO)
        self.assertIsNotNone(registro.fecha)

    def test_registro_como_anfitrion(self):
        self.cliente.post(self.url, datos_registro(rol='Anfitrion'), format='json')
        self.assertTrue(Usuario.objects.get(username='nuevo.usuario').es_anfitrion())

    def test_campos_obligatorios(self):
        respuesta = self.cliente.post(self.url, {}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        for campo in ['nombre_usuario', 'nombres', 'apellidos', 'correo', 'contrasena',
                      'confirmar_contrasena']:
            self.assertIn(campo, respuesta.data)
        self.assertFalse(Usuario.objects.exists())

    def test_datos_invalidos(self):
        casos = {
            'nombres': 'Mar1a', 'apellidos': 'G', 'telefono': '30012abc',
            'correo': 'no-es-correo', 'nombre_usuario': 'con espacio', 'rol': 'Administrador',
            'confirmar_contrasena': 'Otra#Clave2026',
        }
        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                respuesta = self.cliente.post(self.url, datos_registro(**{campo: valor}), format='json')
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.data)
        self.assertFalse(Usuario.objects.exists())

    def test_limites_de_longitud(self):
        respuesta = self.cliente.post(self.url, datos_registro(telefono='123456'), format='json')
        self.assertIn('telefono', respuesta.data)
        respuesta = self.cliente.post(self.url, datos_registro(nombre_usuario='abc'), format='json')
        self.assertIn('nombre_usuario', respuesta.data)
        respuesta = self.cliente.post(self.url, datos_registro(telefono='1234567'), format='json')
        self.assertEqual(respuesta.status_code, 201)

    def test_contrasenas_debiles(self):
        for clave in ['12345678', 'password', 'corta1#', 'nuevo.usuario#A1']:
            with self.subTest(clave=clave):
                respuesta = self.cliente.post(
                    self.url, datos_registro(contrasena=clave, confirmar_contrasena=clave),
                    format='json')
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn('contrasena', respuesta.data)

    def test_correo_duplicado_sin_importar_mayusculas(self):
        crear_usuario(correo='nuevo@correo.com')
        respuesta = self.cliente.post(self.url, datos_registro(correo='NUEVO@correo.com'), format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('correo', respuesta.data)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_nombre_usuario_duplicado(self):
        crear_usuario(nombre='Nuevo.Usuario', correo='otro@correo.com')
        respuesta = self.cliente.post(self.url, datos_registro(), format='json')
        self.assertIn('nombre_usuario', respuesta.data)

    @patch('aplicaciones.gestion_usuario.views.enviar_codigo_verificacion', return_value=False)
    def test_falla_envio_correo_no_impide_registro(self, _):
        respuesta = self.cliente.post(self.url, datos_registro(), format='json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertFalse(respuesta.data['correo_enviado'])


class VerificacionTests(BaseApi):
    url = reverse('verificar_correo')

    def setUp(self):
        super().setUp()
        self.usuario = crear_usuario(verificado=False)
        self.codigo = self.usuario.generar_codigo_verificacion()

    def verificar(self, codigo):
        return self.cliente.post(self.url, {'correo': self.usuario.email, 'codigo': codigo}, format='json')

    def test_codigo_correcto(self):
        self.assertEqual(self.verificar(self.codigo).status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.correo_verificado)
        self.assertIsNotNone(self.ultima_auditoria(Auditoria.Accion.VERIFICACION))

    def test_codigo_incorrecto_suma_intentos_y_bloquea(self):
        incorrecto = '000000' if self.codigo != '000000' else '111111'
        for _ in range(Usuario.MAXIMO_INTENTOS_CODIGO):
            self.assertEqual(self.verificar(incorrecto).status_code, 400)
        self.assertEqual(self.verificar(self.codigo).status_code, 429)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.correo_verificado)

    def test_codigo_vencido(self):
        Usuario.objects.filter(pk=self.usuario.pk).update(
            codigo_enviado=timezone.now() - timedelta(minutes=Usuario.VIGENCIA_CODIGO_MINUTOS + 1))
        self.assertEqual(self.verificar(self.codigo).status_code, 400)

    def test_formato_de_codigo(self):
        self.assertEqual(self.verificar('12ab').status_code, 400)

    def test_ya_verificado(self):
        self.verificar(self.codigo)
        self.assertEqual(self.verificar(self.codigo).status_code, 409)

    def test_reenvio_respeta_espera(self):
        url = reverse('reenviar_codigo')
        self.assertEqual(self.cliente.post(url, {'correo': self.usuario.email}).status_code, 429)
        Usuario.objects.filter(pk=self.usuario.pk).update(
            codigo_enviado=timezone.now() - timedelta(minutes=2))
        self.assertEqual(self.cliente.post(url, {'correo': self.usuario.email}).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)


class IngresoTests(BaseApi):
    url = reverse('ingresar')

    def setUp(self):
        super().setUp()
        self.usuario = crear_usuario()

    def ingresar(self, credencial, clave=CLAVE):
        return self.cliente.post(self.url, {'correo_o_usuario': credencial, 'contrasena': clave},
                                 format='json')

    def test_ingreso_con_correo_y_con_usuario(self):
        for credencial in ['HUESPED1@correo.com', 'Huesped1']:
            with self.subTest(credencial=credencial):
                respuesta = self.ingresar(credencial)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.data['usuario']['rol'], 'Huesped')
        self.assertEqual(Auditoria.objects.filter(accion=Auditoria.Accion.INGRESO).count(), 2)

    def test_credenciales_incorrectas(self):
        for credencial, clave in [('huesped1', 'Otra#Clave1'), ('noexiste@correo.com', CLAVE)]:
            with self.subTest(credencial=credencial):
                respuesta = self.ingresar(credencial, clave)
                self.assertEqual(respuesta.status_code, 401)
                self.assertEqual(respuesta.data['mensaje'], 'Correo, usuario o contraseña incorrectos.')
        fallido = self.ultima_auditoria(Auditoria.Accion.ACCESO_FALLIDO)
        self.assertEqual(fallido.resultado, Auditoria.Resultado.RECHAZADO)
        self.assertEqual(self.cliente.get(reverse('perfil')).status_code, 401)

    def test_rechazos_por_estado(self):
        casos = [
            ({'correo_verificado': False}, 'requiere_verificacion'),
            ({'estado': Usuario.Estado.INACTIVO}, 'requiere_reactivacion'),
            ({'estado': Usuario.Estado.RESTRINGIDO, 'motivo_restriccion': 'Fraude'}, 'estado'),
        ]
        for cambios, clave in casos:
            with self.subTest(cambios=cambios):
                Usuario.objects.filter(pk=self.usuario.pk).update(
                    **{'correo_verificado': True, 'estado': Usuario.Estado.ACTIVO, **cambios})
                respuesta = self.ingresar('huesped1')
                self.assertEqual(respuesta.status_code, 403)
                self.assertIn(clave, respuesta.data)
        self.assertEqual(self.cliente.get(reverse('perfil')).status_code, 401)

    def test_campos_obligatorios(self):
        respuesta = self.cliente.post(self.url, {}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('correo_o_usuario', respuesta.data)
        self.assertIn('contrasena', respuesta.data)

    def test_salir_invalida_la_sesion(self):
        self.ingresar('huesped1')
        self.assertEqual(self.cliente.post(reverse('salir')).status_code, 200)
        self.assertIsNotNone(self.ultima_auditoria(Auditoria.Accion.SALIDA))
        self.assertEqual(self.cliente.get(reverse('perfil')).status_code, 401)

    def test_backend_sin_credenciales(self):
        self.assertIsNone(AutenticacionCorreoOUsuario().authenticate(None, username=None, password=CLAVE))

    def test_csrf_requerido_en_navegador(self):
        cliente = APIClient(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.put(reverse('perfil'), {'nombres': 'Luisa'}, format='json').status_code, 403)


class PerfilTests(BaseApi):
    url = reverse('perfil')

    def setUp(self):
        super().setUp()
        self.usuario = crear_usuario()
        self.cliente.force_login(self.usuario)

    def test_vistas_privadas_sin_sesion(self):
        anonimo = APIClient()
        self.assertEqual(anonimo.get(self.url).status_code, 401)
        self.assertEqual(anonimo.put(self.url, {}).status_code, 401)
        self.assertEqual(anonimo.patch(reverse('desactivar_cuenta')).status_code, 401)
        self.assertEqual(anonimo.get(reverse('admin_usuarios')).status_code, 401)

    def test_consultar_perfil(self):
        datos = self.cliente.get(self.url).data
        self.assertEqual(datos['correo'], 'huesped1@correo.com')
        self.assertNotIn('password', datos)

    def test_actualizar_y_persistir(self):
        respuesta = self.cliente.put(
            self.url, {'nombres': '  Luisa   Fernanda ', 'telefono': '3109876543'}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, 'Luisa Fernanda')
        self.assertEqual(self.usuario.telefono, '3109876543')
        self.assertEqual(self.ultima_auditoria(Auditoria.Accion.ACTUALIZACION_PERFIL).usuario, self.usuario)

    def test_campos_protegidos_no_cambian(self):
        self.cliente.put(self.url, {'correo': 'hack@correo.com', 'estado': 'RESTRINGIDO',
                                    'correo_verificado': False}, format='json')
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, 'huesped1@correo.com')
        self.assertEqual(self.usuario.estado, Usuario.Estado.ACTIVO)
        self.assertTrue(self.usuario.correo_verificado)

    def test_datos_invalidos_no_se_guardan(self):
        for datos in [{'nombres': ''}, {'apellidos': 'P3rez'}, {'telefono': 'abc'}]:
            with self.subTest(datos=datos):
                self.assertEqual(self.cliente.put(self.url, datos, format='json').status_code, 400)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, 'Ana')
        self.assertFalse(Auditoria.objects.filter(accion=Auditoria.Accion.ACTUALIZACION_PERFIL).exists())


class EstadoCuentaTests(BaseApi):
    def setUp(self):
        super().setUp()
        self.usuario = crear_usuario()

    def reactivar(self, clave=CLAVE):
        return self.cliente.post(reverse('reactivar'),
                                 {'correo_o_usuario': 'huesped1', 'contrasena': clave}, format='json')

    def test_desactivar_y_reactivar(self):
        self.cliente.force_login(self.usuario)
        self.assertEqual(self.cliente.patch(reverse('desactivar_cuenta')).status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado, Usuario.Estado.INACTIVO)
        self.assertEqual(self.cliente.get(reverse('perfil')).status_code, 401)

        self.assertEqual(self.reactivar('Mala#Clave1').status_code, 401)
        self.assertEqual(self.reactivar().status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado, Usuario.Estado.ACTIVO)
        self.assertEqual(Auditoria.objects.filter(accion=Auditoria.Accion.CAMBIO_ESTADO).count(), 2)

    def test_reactivar_cuenta_activa_o_restringida(self):
        self.assertEqual(self.reactivar().status_code, 409)
        Usuario.objects.filter(pk=self.usuario.pk).update(estado=Usuario.Estado.RESTRINGIDO)
        self.assertEqual(self.reactivar().status_code, 403)


class AdministracionTests(BaseApi):
    def setUp(self):
        super().setUp()
        self.admin = Usuario.objects.create_superuser('admin', 'admin@correo.com', CLAVE)
        self.usuario = crear_usuario()
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)

    def restringir(self, pk, motivo='Publicó información falsa'):
        return self.cliente.post(reverse('restringir_usuario', args=[pk]), {'motivo': motivo}, format='json')

    def test_superusuario_queda_como_administrador(self):
        self.assertTrue(self.admin.es_administrador())
        self.assertTrue(self.admin.correo_verificado)

    def test_solo_administrador_accede(self):
        for usuario in [self.usuario, self.anfitrion]:
            with self.subTest(usuario=usuario.username):
                self.cliente.force_login(usuario)
                self.assertEqual(self.cliente.get(reverse('admin_usuarios')).status_code, 403)
                self.assertEqual(self.restringir(self.admin.pk).status_code, 403)
        self.cliente.force_login(self.admin)
        respuesta = self.cliente.get(reverse('admin_usuarios'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 3)

    def test_restringir_y_liberar(self):
        self.cliente.force_login(self.admin)
        self.assertEqual(self.restringir(self.usuario.pk).status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado, Usuario.Estado.RESTRINGIDO)
        registro = self.ultima_auditoria(Auditoria.Accion.RESTRICCION)
        self.assertEqual(registro.usuario, self.admin)
        self.assertIn('Publicó información falsa', registro.detalle)

        restringido = APIClient()
        restringido.force_login(self.usuario)
        self.assertEqual(restringido.put(reverse('perfil'), {'nombres': 'Otra'}, format='json').status_code, 403)

        self.assertEqual(self.cliente.post(reverse('liberar_usuario', args=[self.usuario.pk])).status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado, Usuario.Estado.ACTIVO)
        self.assertEqual(self.usuario.motivo_restriccion, '')
        self.assertEqual(self.cliente.post(reverse('liberar_usuario', args=[self.usuario.pk])).status_code, 409)

    def test_restricciones_invalidas(self):
        self.cliente.force_login(self.admin)
        self.assertEqual(self.restringir(self.admin.pk).status_code, 400)
        self.assertEqual(self.restringir(self.usuario.pk, 'malo').status_code, 400)
        self.assertEqual(self.restringir(99999).status_code, 404)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado, Usuario.Estado.ACTIVO)


class RecuperacionTests(BaseApi):
    def setUp(self):
        super().setUp()
        self.usuario = crear_usuario()

    def restablecer(self, token, clave='Nueva#Clave2026'):
        return self.cliente.post(reverse('restablecer'), {
            'correo': self.usuario.email, 'token': token,
            'contrasena': clave, 'confirmar_contrasena': clave}, format='json')

    def test_correo_desconocido_no_revela_nada(self):
        respuesta = self.cliente.post(reverse('recuperar'), {'correo': 'nadie@correo.com'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_flujo_completo_y_enlace_de_un_solo_uso(self):
        self.cliente.post(reverse('recuperar'), {'correo': self.usuario.email})
        self.assertEqual(len(mail.outbox), 1)
        token = re.search(r'token=([\w-]+)', mail.outbox[0].body).group(1)
        self.assertEqual(self.restablecer(token).status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Nueva#Clave2026'))
        self.assertEqual(self.restablecer(token, 'Otra#Clave2027').status_code, 400)
        self.assertEqual(Auditoria.objects.filter(accion=Auditoria.Accion.RECUPERACION).count(), 2)

    def test_token_invalido_y_clave_debil(self):
        self.assertEqual(self.restablecer('token-falso').status_code, 400)
        token = default_token_generator.make_token(self.usuario)
        for clave in ['12345678', 'Huesped1#correo']:
            with self.subTest(clave=clave):
                respuesta = self.restablecer(token, clave)
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn('contrasena', respuesta.data)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(CLAVE))
