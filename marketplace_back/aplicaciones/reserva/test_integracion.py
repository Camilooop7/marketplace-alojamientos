from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from aplicaciones.gestion_usuario.models import Auditoria, Usuario
from aplicaciones.gestion_usuario.tests import CLAVE, crear_usuario
from .models import Factura, Reserva
from .tests import dias, preparar_alojamiento


class IntegracionReservaTests(TestCase):
    def setUp(self):
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        self.huesped = crear_usuario()
        self.otro_huesped = crear_usuario('huesped2', 'huesped2@correo.com')
        self.publicacion, self.desayuno = preparar_alojamiento(self.anfitrion)

    def ingresar(self, usuario):
        cliente = APIClient(enforce_csrf_checks=True)
        cliente.get(reverse('csrf'))
        respuesta = cliente.post(reverse('ingresar'), {'correo_o_usuario': usuario.username, 'contrasena': CLAVE},
                                 format='json', HTTP_X_CSRFTOKEN=cliente.cookies['csrftoken'].value)
        self.assertEqual(respuesta.status_code, 200)
        cliente.credentials(HTTP_X_CSRFTOKEN=cliente.cookies['csrftoken'].value)
        return cliente

    def solicitud(self, entrada=10, salida=13, **cambios):
        datos = {'publicacion': self.publicacion.pk, 'fecha_entrada': dias(entrada), 'fecha_salida': dias(salida),
                 'huespedes': 2, 'servicios': [self.desayuno.pk]}
        datos.update(cambios)
        return datos

    def fechas_ocupadas(self):
        datos = APIClient().get(reverse('calendario', args=[self.publicacion.pk])).data
        return [(str(periodo['inicio']), str(periodo['fin'])) for periodo in datos['reservadas']]

    def test_flujo_cotizar_reservar_factura_y_consultar(self):
        cotizacion = APIClient().post(reverse('cotizacion'), self.solicitud(), format='json')
        self.assertEqual(cotizacion.status_code, 200)
        self.assertEqual(cotizacion.data['total'], '680000.00')

        huesped = self.ingresar(self.huesped)
        respuesta = huesped.post(reverse('reservas'), self.solicitud(clave_idempotencia='flujo-12345678'),
                                 format='json')
        self.assertEqual(respuesta.status_code, 201)
        reserva = Reserva.objects.get(pk=respuesta.data['reserva']['id'])
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE_PAGO)
        self.assertEqual(reserva.total, Decimal(cotizacion.data['total']))
        self.assertEqual(self.fechas_ocupadas(), [(dias(10).isoformat(), dias(13).isoformat())])

        contrato = huesped.get(reverse('factura', args=[reserva.pk])).data
        self.assertEqual(contrato['numero'], reserva.factura.numero)
        self.assertEqual(contrato['total'], '680000.00')
        pdf = huesped.get(contrato['pdf'])
        self.assertEqual(pdf['Content-Type'], 'application/pdf')
        self.assertTrue(pdf.content.startswith(b'%PDF'))

        self.assertEqual([fila['codigo'] for fila in huesped.get(reverse('reservas')).data], [reserva.codigo])
        anfitrion = self.ingresar(self.anfitrion)
        recibidas = anfitrion.get(reverse('reservas_recibidas'), {'estado': 'PENDIENTE_PAGO'}).data
        self.assertEqual([fila['codigo'] for fila in recibidas], [reserva.codigo])
        detalle = anfitrion.get(reverse('reserva', args=[reserva.pk])).data
        self.assertEqual(detalle['historial'][0]['estado_nuevo'], Reserva.Estado.PENDIENTE_PAGO)

        for accion in (Auditoria.Accion.INGRESO, Auditoria.Accion.RESERVA, Auditoria.Accion.FACTURA):
            self.assertTrue(Auditoria.objects.filter(usuario=self.huesped, accion=accion).exists(), accion)

    def test_sin_token_csrf_no_se_crea_la_reserva(self):
        huesped = self.ingresar(self.huesped)
        huesped.credentials()
        respuesta = huesped.post(reverse('reservas'), self.solicitud(), format='json')
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Reserva.objects.exists())

    def test_dos_huespedes_compiten_por_las_mismas_fechas(self):
        primero = self.ingresar(self.huesped)
        segundo = self.ingresar(self.otro_huesped)
        self.assertEqual(primero.post(reverse('reservas'), self.solicitud(), format='json').status_code, 201)
        respuesta = segundo.post(reverse('reservas'), self.solicitud(entrada=11, salida=14), format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('ya está reservado', respuesta.data['fecha_entrada'][0])
        self.assertEqual(segundo.post(reverse('reservas'), self.solicitud(entrada=13, salida=15),
                                      format='json').status_code, 201)
        self.assertEqual(Reserva.objects.count(), 2)

    def test_cancelacion_anula_factura_y_libera_fechas(self):
        huesped = self.ingresar(self.huesped)
        reserva_id = huesped.post(reverse('reservas'), self.solicitud(), format='json').data['reserva']['id']
        respuesta = huesped.post(reverse('cancelacion', args=[reserva_id]), {'motivo': 'Cambié mis planes de viaje'},
                                 format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Factura.objects.get(reserva_id=reserva_id).estado, Factura.Estado.ANULADA)
        self.assertEqual(self.fechas_ocupadas(), [])
        self.assertEqual(huesped.get(reverse('reservas'), {'estado': 'CANCELADA'}).data[0]['id'], reserva_id)

        otro = self.ingresar(self.otro_huesped)
        self.assertEqual(otro.post(reverse('reservas'), self.solicitud(), format='json').status_code, 201)
        self.assertTrue(Auditoria.objects.filter(usuario=self.huesped, accion=Auditoria.Accion.CANCELACION).exists())

