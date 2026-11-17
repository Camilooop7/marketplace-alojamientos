from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from aplicaciones.gestion_usuario.models import Usuario
from aplicaciones.gestion_usuario.tests import CLAVE, crear_usuario
from .models import Disponibilidad, ImagenPublicacion, Publicacion


def crear_publicacion(anfitrion, estado=Publicacion.Estado.ACTIVA, **extra):
    datos = {'titulo': 'Cabaña en el bosque', 'descripcion': 'Cabaña tranquila rodeada de naturaleza.',
             'ciudad': 'Guatapé', 'direccion': 'Vereda El Roble', 'tipo': 'CABANA', 'capacidad': 4,
             'precio_noche': 200000, 'tarifa_limpieza': 50000, 'estado': estado}
    datos.update(extra)
    return Publicacion.objects.create(anfitrion=anfitrion, **datos)


class PublicacionTests(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        self.otro = crear_usuario('anfitrion2', 'anfitrion2@correo.com', Usuario.ROL_ANFITRION)
        self.huesped = crear_usuario()
        self.admin = Usuario.objects.create_superuser('admin', 'admin@correo.com', CLAVE)

    def test_listado_publico_solo_activas_y_filtros(self):
        crear_publicacion(self.anfitrion)
        crear_publicacion(self.anfitrion, titulo='Casa en Bogotá', ciudad='Bogotá', capacidad=2, tipo='CASA')
        crear_publicacion(self.anfitrion, estado=Publicacion.Estado.BORRADOR, titulo='Borrador oculto')
        crear_publicacion(self.anfitrion, estado=Publicacion.Estado.PAUSADA, titulo='Pausada oculta')
        respuesta = self.cliente.get(reverse('publicaciones'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual({p['titulo'] for p in respuesta.data}, {'Cabaña en el bosque', 'Casa en Bogotá'})
        self.assertEqual(len(self.cliente.get(reverse('publicaciones'), {'ciudad': 'bogo'}).data), 1)
        self.assertEqual(len(self.cliente.get(reverse('publicaciones'), {'huespedes': 3}).data), 1)
        self.assertEqual(len(self.cliente.get(reverse('publicaciones'), {'tipo': 'CASA'}).data), 1)

    def test_detalle_de_no_activa_solo_para_dueno_o_admin(self):
        publicacion = crear_publicacion(self.anfitrion, estado=Publicacion.Estado.BORRADOR)
        url = reverse('publicacion', args=[publicacion.pk])
        self.assertEqual(self.cliente.get(url).status_code, 404)
        for usuario, codigo in [(self.otro, 404), (self.anfitrion, 200), (self.admin, 200)]:
            with self.subTest(usuario=usuario.username):
                self.cliente.force_login(usuario)
                self.assertEqual(self.cliente.get(url).status_code, codigo)

    def test_mis_publicaciones(self):
        crear_publicacion(self.anfitrion)
        crear_publicacion(self.otro)
        self.cliente.force_login(self.anfitrion)
        self.assertEqual(len(self.cliente.get(reverse('mis_publicaciones')).data), 1)
        self.cliente.force_login(self.huesped)
        self.assertEqual(self.cliente.get(reverse('mis_publicaciones')).status_code, 403)

    def test_disponibilidad_publica(self):
        publicacion = crear_publicacion(self.anfitrion)
        hoy = timezone.localdate()
        Disponibilidad.objects.create(publicacion=publicacion, fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=30))
        datos = self.cliente.get(reverse('disponibilidad', args=[publicacion.pk])).data
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]['fecha_inicio'], str(hoy))
        self.assertEqual(datos[0]['fecha_fin'], str(hoy + timedelta(days=30)))

    def test_no_se_puede_crear_editar_ni_eliminar(self):
        publicacion = crear_publicacion(self.anfitrion)
        self.cliente.force_login(self.anfitrion)
        url = reverse('publicacion', args=[publicacion.pk])
        casos = [
            self.cliente.post(reverse('publicaciones'), {'titulo': 'Nueva'}, format='json'),
            self.cliente.put(url, {'precio_noche': '1'}, format='json'),
            self.cliente.patch(url, {'precio_noche': '1'}, format='json'),
            self.cliente.delete(url),
            self.cliente.post(reverse('disponibilidad', args=[publicacion.pk]), {}, format='json'),
            self.cliente.post(reverse('imagenes', args=[publicacion.pk]), {}, format='json'),
        ]
        self.assertEqual({respuesta.status_code for respuesta in casos}, {405})
        publicacion.refresh_from_db()
        self.assertEqual(publicacion.precio_noche, 200000)
        self.assertEqual(Publicacion.objects.count(), 1)


class ImagenTests(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        self.publicacion = crear_publicacion(self.anfitrion)
        self.contenido = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b'imagen'
        self.imagen = ImagenPublicacion.objects.create(publicacion=self.publicacion, contenido=self.contenido)
        self.url = reverse('imagen_archivo', args=[self.publicacion.pk, self.imagen.pk])

    def test_detalle_y_listado_incluyen_imagenes_y_el_archivo_es_publico(self):
        detalle = self.cliente.get(reverse('publicacion', args=[self.publicacion.pk]))
        self.assertEqual(detalle.data['imagenes'], [{'id': self.imagen.pk, 'orden': 0}])
        self.assertEqual(self.cliente.get(reverse('publicaciones')).data[0]['imagenes'][0]['id'], self.imagen.pk)
        self.assertEqual(len(self.cliente.get(reverse('imagenes', args=[self.publicacion.pk])).data), 1)
        archivo = self.cliente.get(self.url)
        self.assertEqual(archivo.status_code, 200)
        self.assertEqual(archivo['Content-Type'], 'image/jpeg')
        self.assertEqual(archivo.content, self.contenido)

    def test_archivo_de_publicacion_no_activa_solo_para_el_dueno(self):
        Publicacion.objects.filter(pk=self.publicacion.pk).update(estado=Publicacion.Estado.BORRADOR)
        self.assertEqual(self.cliente.get(self.url).status_code, 404)
        self.cliente.force_login(self.anfitrion)
        self.assertEqual(self.cliente.get(self.url).status_code, 200)
