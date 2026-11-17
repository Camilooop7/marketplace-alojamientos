import threading
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from aplicaciones.gestion_usuario.models import Auditoria, Usuario
from aplicaciones.gestion_usuario.tests import CLAVE, crear_usuario
from aplicaciones.publicacion.models import Disponibilidad, Publicacion, ServicioAdicional
from aplicaciones.publicacion.tests import crear_publicacion
from .calculo import calcular_cotizacion
from .models import Factura, Reserva

HOY = timezone.localdate


def dias(n):
    return HOY() + timedelta(days=n)


def preparar_alojamiento(anfitrion, **extra):
    publicacion = crear_publicacion(anfitrion, **extra)
    Disponibilidad.objects.create(publicacion=publicacion, fecha_inicio=HOY(), fecha_fin=dias(90))
    desayuno = ServicioAdicional.objects.create(publicacion=publicacion, nombre='Desayuno', precio=30000)
    return publicacion, desayuno


class CalculoTests(TestCase):
    def setUp(self):
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        self.publicacion, self.desayuno = preparar_alojamiento(self.anfitrion)

    def test_ejemplo_del_documento_ca_048(self):
        cotizacion = calcular_cotizacion(self.publicacion, dias(5), dias(8), [self.desayuno])
        esperado = {'noches': 3, 'precio_base': Decimal('600000'), 'tarifa_limpieza': Decimal('50000'),
                    'total_servicios': Decimal('30000'), 'descuento': Decimal('0'),
                    'total': Decimal('680000')}
        for clave, valor in esperado.items():
            self.assertEqual(cotizacion[clave], valor, clave)

    def test_descuento_por_estancia_larga_ca_031(self):
        self.publicacion.descuento_porcentaje = 10
        self.publicacion.noches_descuento = 7
        siete = calcular_cotizacion(self.publicacion, dias(1), dias(8))
        seis = calcular_cotizacion(self.publicacion, dias(1), dias(7))
        self.assertEqual(siete['descuento'], Decimal('140000'))
        self.assertEqual(siete['total'], Decimal('1400000') - Decimal('140000') + Decimal('50000'))
        self.assertEqual(seis['descuento'], Decimal('0'))


class BaseReserva(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        self.huesped = crear_usuario()
        self.otro_huesped = crear_usuario('huesped2', 'huesped2@correo.com')
        self.admin = Usuario.objects.create_superuser('admin', 'admin@correo.com', CLAVE)
        self.publicacion, self.desayuno = preparar_alojamiento(self.anfitrion)

    def solicitud(self, entrada=10, salida=13, **cambios):
        datos = {'publicacion': self.publicacion.pk, 'fecha_entrada': dias(entrada),
                 'fecha_salida': dias(salida), 'huespedes': 2, 'servicios': [self.desayuno.pk]}
        datos.update(cambios)
        return datos

    def reservar(self, usuario=None, **cambios):
        self.cliente.force_login(usuario or self.huesped)
        return self.cliente.post(reverse('reservas'), self.solicitud(**cambios), format='json')


class CotizacionTests(BaseReserva):
    url = reverse('cotizacion')

    def test_cotizacion_publica_y_desglosada(self):
        respuesta = APIClient().post(self.url, self.solicitud(), format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['noches'], 3)
        self.assertEqual(respuesta.data['total'], '680000.00')
        self.assertFalse(Reserva.objects.exists())

    def test_solicitudes_invalidas(self):
        _, servicio_ajeno = preparar_alojamiento(self.anfitrion, titulo='Otra cabaña')
        casos = [
            ({'huespedes': 5}, 'huespedes', 'La capacidad máxima es de 4 huéspedes.'),
            ({'entrada': 10, 'salida': 10}, 'fecha_salida', None),
            ({'entrada': -1, 'salida': 2}, 'fecha_entrada', None),
            ({'entrada': 85, 'salida': 95}, 'fecha_entrada', None),
            ({'servicios': [servicio_ajeno.pk]}, 'servicios', None),
            ({'publicacion': 99999}, 'publicacion', None),
            ({'huespedes': 0}, 'huespedes', None),
        ]
        for cambios, campo, mensaje in casos:
            with self.subTest(cambios=cambios):
                respuesta = APIClient().post(self.url, self.solicitud(**cambios), format='json')
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.data)
                if mensaje:
                    self.assertEqual(respuesta.data[campo][0], mensaje)

    def test_publicacion_no_activa(self):
        Publicacion.objects.filter(pk=self.publicacion.pk).update(estado=Publicacion.Estado.PAUSADA)
        respuesta = APIClient().post(self.url, self.solicitud(), format='json')
        self.assertIn('publicacion', respuesta.data)


class CrearReservaTests(BaseReserva):
    def test_reserva_completa_hasta_la_factura(self):
        respuesta = self.reservar()
        self.assertEqual(respuesta.status_code, 201)
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.huesped, self.huesped)
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE_PAGO)
        self.assertRegex(reserva.codigo, r'^RES-[0-9A-F]{8}$')
        self.assertEqual(reserva.total, Decimal('680000'))
        self.assertEqual(reserva.servicios, [{'nombre': 'Desayuno', 'precio': '30000.00'}])
        factura = reserva.factura
        self.assertRegex(factura.numero, r'^FAC-\d{4}-\d{6}$')
        self.assertEqual(factura.total, reserva.total)
        self.assertEqual(factura.estado, Factura.Estado.EMITIDA)
        self.assertEqual(factura.cliente_correo, self.huesped.email)
        self.assertEqual(respuesta.data['reserva']['factura'], factura.numero)
        self.assertEqual(reserva.historial.get().estado_nuevo, Reserva.Estado.PENDIENTE_PAGO)
        for accion in [Auditoria.Accion.RESERVA, Auditoria.Accion.FACTURA]:
            self.assertTrue(Auditoria.objects.filter(accion=accion, usuario=self.huesped).exists())

    def test_permisos_para_reservar(self):
        self.assertEqual(APIClient().post(reverse('reservas'), self.solicitud(), format='json').status_code, 401)
        Usuario.objects.filter(pk=self.huesped.pk).update(estado=Usuario.Estado.RESTRINGIDO)
        self.assertEqual(self.reservar().status_code, 403)
        self.assertFalse(Reserva.objects.exists())

    def test_anfitrion_reserva_en_otra_publicacion(self):
        otro_anfitrion = crear_usuario('anfitrion2', 'anfitrion2@correo.com', Usuario.ROL_ANFITRION)
        respuesta = self.reservar(otro_anfitrion)
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(Reserva.objects.get().huesped, otro_anfitrion)

    def test_no_reserva_su_propia_publicacion_pero_si_la_cotiza(self):
        respuesta = self.reservar(self.anfitrion)
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data['publicacion'][0], 'No puedes reservar tu propia publicación.')
        cotizacion = self.cliente.post(reverse('cotizacion'), self.solicitud(), format='json')
        self.assertEqual(cotizacion.status_code, 200)

    def test_sin_reservas_dobles(self):
        self.assertEqual(self.reservar().status_code, 201)
        for entrada, salida in [(10, 13), (11, 12), (8, 11), (12, 20)]:
            with self.subTest(entrada=entrada, salida=salida):
                respuesta = self.reservar(self.otro_huesped, entrada=entrada, salida=salida)
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn('ya está reservado', respuesta.data['fecha_entrada'][0])
        self.assertEqual(self.reservar(self.otro_huesped, entrada=13, salida=15).status_code, 201)
        self.assertEqual(self.reservar(self.otro_huesped, entrada=7, salida=10).status_code, 201)
        self.assertEqual(Reserva.objects.count(), 3)

    def test_solicitud_repetida_devuelve_la_misma_reserva_ca_052(self):
        clave = 'a1b2c3d4-e5f6-7890'
        respuestas = [self.reservar(clave_idempotencia=clave) for _ in range(3)]
        self.assertEqual([r.status_code for r in respuestas], [201, 200, 200])
        self.assertEqual(len({r.data['reserva']['id'] for r in respuestas}), 1)
        self.assertEqual(Reserva.objects.count(), 1)
        self.assertEqual(Factura.objects.count(), 1)

    def test_cambio_de_precio_no_altera_reservas_ca_021(self):
        self.reservar()
        Publicacion.objects.filter(pk=self.publicacion.pk).update(precio_noche=400000)
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.precio_noche, Decimal('200000'))
        self.assertEqual(reserva.total, Decimal('680000'))
        self.assertEqual(reserva.factura.total, Decimal('680000'))


class ConsultaReservaTests(BaseReserva):
    def setUp(self):
        super().setUp()
        self.reserva = Reserva.objects.get(pk=self.reservar().data['reserva']['id'])
        self.reservar(self.otro_huesped, entrada=20, salida=22)
        otra, _ = preparar_alojamiento(crear_usuario('anfitrion2', 'anfitrion2@correo.com', Usuario.ROL_ANFITRION))
        self.reservar(publicacion=otra.pk, servicios=[], entrada=30, salida=31)

    def test_mis_reservas_solo_las_propias(self):
        self.cliente.force_login(self.huesped)
        datos = self.cliente.get(reverse('reservas')).data
        self.assertEqual(len(datos), 2)
        self.assertEqual({'codigo', 'publicacion', 'fecha_entrada', 'total', 'estado'} - set(datos[0]), set())
        self.assertEqual(len(self.cliente.get(reverse('reservas'), {'estado': 'CANCELADA'}).data), 0)
        self.assertEqual(len(self.cliente.get(reverse('reservas'), {'estado': 'PENDIENTE_PAGO'}).data), 2)

    def test_reservas_recibidas_del_anfitrion(self):
        self.cliente.force_login(self.anfitrion)
        url = reverse('reservas_recibidas')
        self.assertEqual(len(self.cliente.get(url).data), 2)
        self.assertEqual(len(self.cliente.get(url, {'desde': dias(15), 'hasta': dias(25)}).data), 1)
        self.assertEqual(self.cliente.get(url).data[0]['huesped'], 'Ana Pérez')
        self.cliente.force_login(self.huesped)
        self.assertEqual(self.cliente.get(url).status_code, 403)

    def test_detalle_con_historial_y_privacidad(self):
        url = reverse('reserva', args=[self.reserva.pk])
        for usuario, codigo in [(self.huesped, 200), (self.anfitrion, 200), (self.admin, 200),
                                (self.otro_huesped, 404)]:
            with self.subTest(usuario=usuario.username):
                self.cliente.force_login(usuario)
                respuesta = self.cliente.get(url)
                self.assertEqual(respuesta.status_code, codigo)
        self.cliente.force_login(self.huesped)
        historial = self.cliente.get(url).data['historial']
        self.assertEqual(historial[0]['usuario'], 'Ana Pérez')

    def test_calendario_publico(self):
        datos = APIClient().get(reverse('calendario', args=[self.publicacion.pk])).data
        self.assertEqual(len(datos['disponibles']), 1)
        self.assertEqual([r['inicio'] for r in datos['reservadas']], [dias(10), dias(20)])
        self.assertNotIn('huesped', datos['reservadas'][0])


class CancelacionTests(BaseReserva):
    def setUp(self):
        super().setUp()
        self.reserva = Reserva.objects.get(pk=self.reservar().data['reserva']['id'])
        self.url = reverse('cancelacion', args=[self.reserva.pk])
        self.cliente.force_login(self.huesped)

    def test_cancelar_libera_fechas_y_anula_factura(self):
        respuesta = self.cliente.post(self.url, {'motivo': 'Cambié mis planes de viaje'}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, Reserva.Estado.CANCELADA)
        self.assertEqual(self.reserva.motivo_cancelacion, 'Cambié mis planes de viaje')
        self.assertIsNotNone(self.reserva.fecha_cancelacion)
        self.assertEqual(self.reserva.factura.estado, Factura.Estado.ANULADA)
        self.assertEqual([h.estado_nuevo for h in self.reserva.historial.all()],
                         [Reserva.Estado.PENDIENTE_PAGO, Reserva.Estado.CANCELADA])
        self.assertTrue(Auditoria.objects.filter(accion=Auditoria.Accion.CANCELACION).exists())
        self.assertEqual(self.reservar(self.otro_huesped).status_code, 201)
        self.cliente.force_login(self.huesped)
        self.assertEqual(self.cliente.post(self.url, {'motivo': 'Otra vez'}, format='json').status_code, 409)

    def test_cancelaciones_no_permitidas(self):
        self.assertEqual(self.cliente.post(self.url, {'motivo': 'no'}, format='json').status_code, 400)
        self.cliente.force_login(self.anfitrion)
        self.assertEqual(self.cliente.post(self.url, {'motivo': 'No puedo recibirlos'}, format='json').status_code, 403)
        self.cliente.force_login(self.otro_huesped)
        self.assertEqual(self.cliente.post(self.url, {'motivo': 'Intento ajeno'}, format='json').status_code, 404)
        Reserva.objects.filter(pk=self.reserva.pk).update(fecha_entrada=HOY(), fecha_salida=dias(2))
        self.cliente.force_login(self.huesped)
        self.assertEqual(self.cliente.post(self.url, {'motivo': 'Ya estoy aquí'}, format='json').status_code, 409)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, Reserva.Estado.PENDIENTE_PAGO)


class FacturaTests(BaseReserva):
    def setUp(self):
        super().setUp()
        self.reserva = Reserva.objects.get(pk=self.reservar().data['reserva']['id'])

    def test_contrato_para_el_modulo_de_pagos(self):
        datos = self.cliente.get(reverse('factura', args=[self.reserva.pk])).data
        self.assertEqual(datos['numero'], self.reserva.factura.numero)
        self.assertEqual(datos['reserva_id'], self.reserva.pk)
        self.assertEqual(datos['reserva_codigo'], self.reserva.codigo)
        self.assertEqual(datos['cliente'], {'id': self.huesped.pk, 'nombre': 'Ana Pérez',
                                            'correo': self.huesped.email})
        self.assertEqual(datos['total'], '680000.00')
        self.assertEqual(datos['estado'], 'EMITIDA')
        self.assertEqual(datos['pdf'], reverse('factura_pdf', args=[self.reserva.pk]))

    def test_pdf_generado(self):
        respuesta = self.cliente.get(reverse('factura_pdf', args=[self.reserva.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertIn(self.reserva.factura.numero, respuesta['Content-Disposition'])
        self.assertTrue(respuesta.content.startswith(b'%PDF'))
        self.assertIn(self.reserva.factura.numero.encode(), respuesta.content)
        self.assertGreater(len(respuesta.content), 1500)

    def test_acceso_a_la_factura(self):
        url = reverse('factura_pdf', args=[self.reserva.pk])
        self.assertEqual(APIClient().get(url).status_code, 401)
        self.cliente.force_login(self.otro_huesped)
        self.assertEqual(self.cliente.get(url).status_code, 404)
        self.cliente.force_login(self.anfitrion)
        self.assertEqual(self.cliente.get(url).status_code, 200)


class DesactivarConReservasTests(BaseReserva):
    def test_no_desactiva_con_reservas_pendientes_ca_013_014(self):
        codigo = self.reservar().data['reserva']['codigo']
        for usuario in [self.huesped, self.anfitrion]:
            with self.subTest(usuario=usuario.username):
                self.cliente.force_login(usuario)
                respuesta = self.cliente.patch(reverse('desactivar_cuenta'))
                self.assertEqual(respuesta.status_code, 409)
                self.assertEqual(respuesta.data['reservas'], [codigo])
                usuario.refresh_from_db()
                self.assertEqual(usuario.estado, Usuario.Estado.ACTIVO)

    def test_desactivar_anfitrion_pausa_publicaciones(self):
        self.cliente.force_login(self.anfitrion)
        self.assertEqual(self.cliente.patch(reverse('desactivar_cuenta')).status_code, 200)
        self.publicacion.refresh_from_db()
        self.assertEqual(self.publicacion.estado, Publicacion.Estado.PAUSADA)


class ConcurrenciaTests(TransactionTestCase):
    ROLES = [Usuario.ROL_HUESPED, Usuario.ROL_ANFITRION, Usuario.ROL_ADMINISTRADOR]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for rol in cls.ROLES:
            Group.objects.get_or_create(name=rol)

    def test_solicitudes_simultaneas(self):
        for rol in self.ROLES:
            Group.objects.get_or_create(name=rol)
        anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        publicacion, _ = preparar_alojamiento(anfitrion)
        huespedes = [crear_usuario('huesped{0}'.format(i), 'huesped{0}@correo.com'.format(i)) for i in range(5)]
        resultados = []
        barrera = threading.Barrier(len(huespedes))

        def reservar(usuario):
            cliente = APIClient()
            cliente.force_login(usuario)
            barrera.wait()
            respuesta = cliente.post(reverse('reservas'), {
                'publicacion': publicacion.pk, 'fecha_entrada': dias(10), 'fecha_salida': dias(12),
                'huespedes': 1}, format='json')
            resultados.append(respuesta.status_code)
            connection.close()

        hilos = [threading.Thread(target=reservar, args=[usuario]) for usuario in huespedes]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        self.assertEqual(resultados.count(201), 1, resultados)
        self.assertEqual(Reserva.objects.filter(publicacion=publicacion).count(), 1)
