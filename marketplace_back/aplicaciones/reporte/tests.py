from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from aplicaciones.gestion_usuario.models import Usuario
from aplicaciones.gestion_usuario.tests import CLAVE, crear_usuario
from aplicaciones.publicacion.tests import crear_publicacion
from aplicaciones.reserva.calculo import calcular_cotizacion
from aplicaciones.reserva.models import Reserva


def dias(n):
    return timezone.localdate() + timedelta(days=n)


def crear_reserva(publicacion, huesped, entrada, noches, huespedes=2, estado=Reserva.Estado.PENDIENTE_PAGO):
    cotizacion = calcular_cotizacion(publicacion, dias(entrada), dias(entrada + noches))
    return Reserva.objects.create(publicacion=publicacion, huesped=huesped, fecha_entrada=dias(entrada),
                                  fecha_salida=dias(entrada + noches), huespedes=huespedes, estado=estado,
                                  **cotizacion)


class BaseReporte(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        self.otro_anfitrion = crear_usuario('anfitrion2', 'anfitrion2@correo.com', Usuario.ROL_ANFITRION)
        self.huesped = crear_usuario()
        self.otro_huesped = crear_usuario('huesped2', 'huesped2@correo.com')
        self.admin = Usuario.objects.create_superuser('admin', 'admin@correo.com', CLAVE)
        self.cabana = crear_publicacion(self.anfitrion)
        self.casa = crear_publicacion(self.anfitrion, titulo='Casa en la playa', tipo='CASA', ciudad='Santa Marta',
                                      precio_noche=300000, tarifa_limpieza=0)
        self.ajena = crear_publicacion(self.otro_anfitrion, titulo='Apartamento central', tipo='APARTAMENTO')
        crear_reserva(self.cabana, self.huesped, 5, 3, huespedes=2)
        crear_reserva(self.casa, self.otro_huesped, 40, 2, huespedes=4, estado=Reserva.Estado.CONFIRMADA)
        crear_reserva(self.cabana, self.otro_huesped, 60, 4, estado=Reserva.Estado.CANCELADA)
        crear_reserva(self.ajena, self.huesped, 10, 1)


class ReporteAnfitrionTests(BaseReporte):
    def test_resumen_de_ingresos_personas_y_noches(self):
        self.cliente.force_login(self.anfitrion)
        datos = self.cliente.get(reverse('mi_reporte')).data
        resumen = datos['resumen']
        self.assertEqual(resumen['reservas'], 3)
        self.assertEqual(resumen['canceladas'], 1)
        self.assertEqual(Decimal(resumen['ingresos']), Decimal('650000') + Decimal('600000'))
        self.assertEqual(Decimal(resumen['ingresos_confirmados']), Decimal('600000'))
        self.assertEqual(Decimal(resumen['ingresos_pendientes']), Decimal('650000'))
        self.assertEqual(resumen['noches'], 5)
        self.assertEqual(resumen['huespedes'], 6)
        self.assertEqual(resumen['clientes'], 2)
        self.assertEqual(resumen['reservas_vigentes'], 2)
        self.assertEqual(resumen['alojamientos'], 2)

    def test_agrupa_por_alojamiento_cliente_y_mes(self):
        self.cliente.force_login(self.anfitrion)
        datos = self.cliente.get(reverse('mi_reporte')).data
        self.assertEqual([fila['titulo'] for fila in datos['alojamientos']],
                         ['Cabaña en el bosque', 'Casa en la playa'])
        self.assertEqual(datos['alojamientos'][0]['canceladas'], 1)
        self.assertEqual([fila['nombre'] for fila in datos['clientes']], ['Ana Pérez', 'Ana Pérez'])
        self.assertEqual(sum(Decimal(mes['ingresos']) for mes in datos['meses']), Decimal('1250000'))
        self.assertEqual(len(datos['reservas']), 3)
        self.assertEqual({dato['estado']: dato['cantidad'] for dato in datos['estados']}[Reserva.Estado.CANCELADA], 1)

    def test_no_incluye_reservas_de_otros_anfitriones(self):
        self.cliente.force_login(self.otro_anfitrion)
        datos = self.cliente.get(reverse('mi_reporte')).data
        self.assertEqual(datos['resumen']['reservas'], 1)
        self.assertEqual([fila['alojamiento'] for fila in datos['reservas']], ['Apartamento central'])

    def test_filtra_por_fecha_de_entrada(self):
        self.cliente.force_login(self.anfitrion)
        datos = self.cliente.get(reverse('mi_reporte'), {'desde': dias(30), 'hasta': dias(50)}).data
        self.assertEqual(datos['resumen']['reservas'], 1)
        self.assertEqual(datos['reservas'][0]['alojamiento'], 'Casa en la playa')
        self.assertEqual(datos['periodo'], {'desde': dias(30).isoformat(), 'hasta': dias(50).isoformat()})

    def test_rechaza_fechas_invalidas(self):
        self.cliente.force_login(self.anfitrion)
        invertidas = self.cliente.get(reverse('mi_reporte'), {'desde': dias(10), 'hasta': dias(1)})
        self.assertEqual(invertidas.status_code, 400)
        self.assertIn('posterior', invertidas.data['mensaje'])
        self.assertEqual(self.cliente.get(reverse('mi_reporte'), {'desde': '2026-13-40'}).status_code, 400)

    def test_descarga_pdf(self):
        self.cliente.force_login(self.anfitrion)
        respuesta = self.cliente.get(reverse('mi_reporte_pdf'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertIn('reporte-anfitrion1.pdf', respuesta['Content-Disposition'])
        self.assertTrue(respuesta.content.startswith(b'%PDF'))

    def test_huesped_no_tiene_reporte(self):
        self.cliente.force_login(self.huesped)
        self.assertEqual(self.cliente.get(reverse('mi_reporte')).status_code, 403)
        self.assertEqual(self.cliente.get(reverse('mi_reporte_pdf')).status_code, 403)

    def test_requiere_sesion(self):
        self.assertIn(self.cliente.get(reverse('mi_reporte')).status_code, (401, 403))


class ReporteAdministradorTests(BaseReporte):
    def test_resumen_general_por_anfitrion(self):
        self.cliente.force_login(self.admin)
        datos = self.cliente.get(reverse('reporte_general')).data
        self.assertEqual(datos['resumen']['anfitriones'], 2)
        self.assertEqual(datos['resumen']['reservas'], 4)
        self.assertEqual(datos['resumen']['alojamientos'], 3)
        filas = {fila['usuario']: fila for fila in datos['anfitriones']}
        self.assertEqual(Decimal(filas['anfitrion1']['ingresos']), Decimal('1250000'))
        self.assertEqual(filas['anfitrion2']['reservas'], 1)
        self.assertEqual(datos['anfitriones'][0]['usuario'], 'anfitrion1')

    def test_reporte_de_un_anfitrion(self):
        self.cliente.force_login(self.admin)
        datos = self.cliente.get(reverse('reporte_anfitrion', args=[self.anfitrion.pk])).data
        self.assertEqual(datos['anfitrion']['usuario'], 'anfitrion1')
        self.assertEqual(datos['resumen']['reservas'], 3)

    def test_solo_anfitriones(self):
        self.cliente.force_login(self.admin)
        respuesta = self.cliente.get(reverse('reporte_anfitrion', args=[self.huesped.pk]))
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.data['mensaje'], 'No encontramos ese anfitrión.')

    def test_descarga_pdfs(self):
        self.cliente.force_login(self.admin)
        for ruta in (reverse('reporte_general_pdf'), reverse('reporte_anfitrion_pdf', args=[self.anfitrion.pk])):
            respuesta = self.cliente.get(ruta, {'desde': dias(0)})
            self.assertEqual(respuesta.status_code, 200)
            self.assertTrue(respuesta.content.startswith(b'%PDF'))
            self.assertIn(dias(0).isoformat(), respuesta['Content-Disposition'])

    def test_anfitrion_no_ve_reportes_de_otros(self):
        self.cliente.force_login(self.anfitrion)
        for ruta in (reverse('reporte_general'), reverse('reporte_general_pdf'),
                     reverse('reporte_anfitrion', args=[self.otro_anfitrion.pk]),
                     reverse('reporte_anfitrion_pdf', args=[self.otro_anfitrion.pk])):
            self.assertEqual(self.cliente.get(ruta).status_code, 403)

    def test_cuenta_vacia(self):
        self.cliente.force_login(self.admin)
        Reserva.objects.all().delete()
        datos = self.cliente.get(reverse('reporte_general')).data
        self.assertEqual(datos['resumen']['ingresos'], '0')
        self.assertEqual(datos['meses'], [])
        self.assertTrue(self.cliente.get(reverse('reporte_general_pdf')).content.startswith(b'%PDF'))
        self.assertTrue(self.cliente.get(reverse('reporte_anfitrion_pdf', args=[self.anfitrion.pk]))
                        .content.startswith(b'%PDF'))
