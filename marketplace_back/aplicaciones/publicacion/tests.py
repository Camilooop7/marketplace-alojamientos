from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from aplicaciones.gestion_usuario.models import Auditoria, Usuario
from aplicaciones.gestion_usuario.tests import CLAVE, crear_usuario
from .models import ImagenPublicacion, Publicacion


def datos_publicacion(**cambios):
    datos = {
        'titulo': 'Apartamento con vista al mar', 'descripcion': 'Apartamento amplio a dos cuadras de la playa.',
        'ciudad': 'Santa Marta', 'direccion': 'Calle 22 # 3-15', 'tipo': 'APARTAMENTO', 'capacidad': 4,
        'precio_noche': '200000', 'tarifa_limpieza': '50000',
        'servicios': [{'nombre': 'Desayuno', 'precio': '30000'}],
    }
    datos.update(cambios)
    return datos


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

    def test_anfitrion_crea_en_borrador_con_servicios(self):
        self.cliente.force_login(self.anfitrion)
        respuesta = self.cliente.post(reverse('publicaciones'), datos_publicacion(), format='json')
        self.assertEqual(respuesta.status_code, 201)
        publicacion = Publicacion.objects.get()
        self.assertEqual(publicacion.anfitrion, self.anfitrion)
        self.assertEqual(publicacion.estado, Publicacion.Estado.BORRADOR)
        self.assertEqual(publicacion.servicios.get().nombre, 'Desayuno')
        self.assertTrue(Auditoria.objects.filter(accion=Auditoria.Accion.PUBLICACION, usuario=self.anfitrion).exists())

    def test_huesped_y_anonimo_no_pueden_crear(self):
        self.assertEqual(self.cliente.post(reverse('publicaciones'), datos_publicacion(), format='json').status_code, 401)
        self.cliente.force_login(self.huesped)
        self.assertEqual(self.cliente.post(reverse('publicaciones'), datos_publicacion(), format='json').status_code, 403)
        self.assertFalse(Publicacion.objects.exists())

    def test_datos_invalidos(self):
        self.cliente.force_login(self.anfitrion)
        casos = {
            'capacidad': 0, 'precio_noche': '0', 'tarifa_limpieza': '-1', 'titulo': 'Casa',
            'ciudad': 'Bogotá 2', 'tipo': 'CASTILLO', 'descripcion': 'Corta',
            'descuento_porcentaje': 95, 'estado': 'BLOQUEADA',
            'servicios': [{'nombre': 'Desayuno', 'precio': '-5'}],
        }
        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                respuesta = self.cliente.post(reverse('publicaciones'), datos_publicacion(**{campo: valor}),
                                              format='json')
                self.assertEqual(respuesta.status_code, 400)
                self.assertIn(campo, respuesta.data)
        respuesta = self.cliente.post(reverse('publicaciones'), datos_publicacion(descripcion='Texto <script>x</script> largo'), format='json')
        self.assertIn('descripcion', respuesta.data)
        self.assertFalse(Publicacion.objects.exists())

    def test_listado_publico_solo_activas_y_filtros(self):
        crear_publicacion(self.anfitrion)
        crear_publicacion(self.anfitrion, titulo='Casa en Bogotá', ciudad='Bogotá', capacidad=2)
        crear_publicacion(self.anfitrion, estado=Publicacion.Estado.BORRADOR, titulo='Borrador oculto')
        crear_publicacion(self.anfitrion, estado=Publicacion.Estado.PAUSADA, titulo='Pausada oculta')
        respuesta = self.cliente.get(reverse('publicaciones'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual({p['titulo'] for p in respuesta.data}, {'Cabaña en el bosque', 'Casa en Bogotá'})
        self.assertEqual(len(self.cliente.get(reverse('publicaciones'), {'ciudad': 'bogo'}).data), 1)
        self.assertEqual(len(self.cliente.get(reverse('publicaciones'), {'huespedes': 3}).data), 1)

    def test_detalle_de_no_activa_solo_para_dueno_o_admin(self):
        publicacion = crear_publicacion(self.anfitrion, estado=Publicacion.Estado.BORRADOR)
        url = reverse('publicacion', args=[publicacion.pk])
        self.assertEqual(self.cliente.get(url).status_code, 404)
        for usuario, codigo in [(self.otro, 404), (self.anfitrion, 200), (self.admin, 200)]:
            with self.subTest(usuario=usuario.username):
                self.cliente.force_login(usuario)
                self.assertEqual(self.cliente.get(url).status_code, codigo)

    def test_editar_registra_valores_anteriores(self):
        publicacion = crear_publicacion(self.anfitrion)
        self.cliente.force_login(self.anfitrion)
        respuesta = self.cliente.put(reverse('publicacion', args=[publicacion.pk]),
                                     {'precio_noche': '250000', 'estado': 'PAUSADA'}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        publicacion.refresh_from_db()
        self.assertEqual(publicacion.precio_noche, 250000)
        detalle = Auditoria.objects.filter(accion=Auditoria.Accion.PUBLICACION).latest('id').detalle
        self.assertIn('precio_noche: 200000.00 -> 250000', detalle)
        self.assertIn('estado: ACTIVA -> PAUSADA', detalle)

    def test_permisos_de_edicion(self):
        publicacion = crear_publicacion(self.anfitrion)
        url = reverse('publicacion', args=[publicacion.pk])
        for usuario, codigo in [(self.otro, 403), (self.huesped, 403), (self.admin, 200)]:
            with self.subTest(usuario=usuario.username):
                self.cliente.force_login(usuario)
                self.assertEqual(self.cliente.put(url, {'capacidad': 3}, format='json').status_code, codigo)

    def test_bloqueada_no_la_edita_el_anfitrion(self):
        publicacion = crear_publicacion(self.anfitrion, estado=Publicacion.Estado.BLOQUEADA)
        self.cliente.force_login(self.anfitrion)
        respuesta = self.cliente.put(reverse('publicacion', args=[publicacion.pk]), {'estado': 'ACTIVA'}, format='json')
        self.assertEqual(respuesta.status_code, 403)
        publicacion.refresh_from_db()
        self.assertEqual(publicacion.estado, Publicacion.Estado.BLOQUEADA)

    def test_mis_publicaciones(self):
        crear_publicacion(self.anfitrion)
        crear_publicacion(self.otro)
        self.cliente.force_login(self.anfitrion)
        self.assertEqual(len(self.cliente.get(reverse('mis_publicaciones')).data), 1)
        self.cliente.force_login(self.huesped)
        self.assertEqual(self.cliente.get(reverse('mis_publicaciones')).status_code, 403)

    def test_disponibilidad_sin_cruces(self):
        publicacion = crear_publicacion(self.anfitrion)
        url = reverse('disponibilidad', args=[publicacion.pk])
        hoy = timezone.localdate()
        self.cliente.force_login(self.anfitrion)
        periodo = {'fecha_inicio': hoy, 'fecha_fin': hoy + timedelta(days=30)}
        self.assertEqual(self.cliente.post(url, periodo, format='json').status_code, 201)
        cruce = self.cliente.post(url, {'fecha_inicio': hoy + timedelta(days=10),
                                        'fecha_fin': hoy + timedelta(days=40)}, format='json')
        self.assertEqual(cruce.status_code, 400)
        self.assertIn('se cruza', cruce.data['fecha_inicio'][0])
        invertido = self.cliente.post(url, {'fecha_inicio': hoy + timedelta(days=50),
                                            'fecha_fin': hoy + timedelta(days=45)}, format='json')
        self.assertIn('fecha_fin', invertido.data)
        contiguo = self.cliente.post(url, {'fecha_inicio': hoy + timedelta(days=30),
                                           'fecha_fin': hoy + timedelta(days=40)}, format='json')
        self.assertEqual(contiguo.status_code, 201)
        self.assertEqual(len(APIClient().get(url).data), 2)
        self.cliente.force_login(self.otro)
        self.assertEqual(self.cliente.post(url, {'fecha_inicio': hoy + timedelta(days=60),
                                                 'fecha_fin': hoy + timedelta(days=70)}, format='json').status_code, 403)


def archivo_imagen(nombre='foto.png', formato='PNG', tamano=(2400, 1200), modo='RGBA'):
    contenido = BytesIO()
    Image.new(modo, tamano, (30, 120, 90, 255) if modo == 'RGBA' else (30, 120, 90)).save(contenido, formato)
    return SimpleUploadedFile(nombre, contenido.getvalue())


class ImagenTests(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.anfitrion = crear_usuario('anfitrion1', 'anfitrion1@correo.com', Usuario.ROL_ANFITRION)
        self.otro = crear_usuario('anfitrion2', 'anfitrion2@correo.com', Usuario.ROL_ANFITRION)
        self.publicacion = crear_publicacion(self.anfitrion)
        self.url = reverse('imagenes', args=[self.publicacion.pk])

    def subir(self, archivo):
        return self.cliente.post(self.url, {'imagen': archivo}, format='multipart')

    def test_anfitrion_sube_y_se_reduce_a_jpeg(self):
        self.cliente.force_login(self.anfitrion)
        respuesta = self.subir(archivo_imagen())
        self.assertEqual(respuesta.status_code, 201)
        imagen = ImagenPublicacion.objects.get(pk=respuesta.data['imagen']['id'])
        guardada = Image.open(BytesIO(bytes(imagen.contenido)))
        self.assertEqual(guardada.format, 'JPEG')
        self.assertEqual(max(guardada.size), 1600)
        self.assertEqual(self.subir(archivo_imagen('otra.jpg', 'JPEG', modo='RGB')).data['imagen']['orden'], 1)
        self.assertTrue(Auditoria.objects.filter(detalle__startswith='Agregó la imagen').exists())

    def test_detalle_y_listado_incluyen_imagenes_y_el_archivo_es_publico(self):
        self.cliente.force_login(self.anfitrion)
        imagen_id = self.subir(archivo_imagen()).data['imagen']['id']
        self.cliente.logout()
        detalle = self.cliente.get(reverse('publicacion', args=[self.publicacion.pk]))
        self.assertEqual(detalle.data['imagenes'], [{'id': imagen_id, 'orden': 0}])
        self.assertEqual(self.cliente.get(reverse('publicaciones')).data[0]['imagenes'][0]['id'], imagen_id)
        archivo = self.cliente.get(reverse('imagen_archivo', args=[self.publicacion.pk, imagen_id]))
        self.assertEqual(archivo.status_code, 200)
        self.assertEqual(archivo['Content-Type'], 'image/jpeg')
        self.assertTrue(archivo.content.startswith(b'\xff\xd8'))

    def test_archivo_de_publicacion_no_activa_solo_para_el_dueno(self):
        self.cliente.force_login(self.anfitrion)
        imagen_id = self.subir(archivo_imagen()).data['imagen']['id']
        Publicacion.objects.filter(pk=self.publicacion.pk).update(estado=Publicacion.Estado.BORRADOR)
        url = reverse('imagen_archivo', args=[self.publicacion.pk, imagen_id])
        self.assertEqual(self.cliente.get(url).status_code, 200)
        self.cliente.logout()
        self.assertEqual(self.cliente.get(url).status_code, 404)

    def test_archivos_invalidos(self):
        self.cliente.force_login(self.anfitrion)
        casos = [
            (SimpleUploadedFile('virus.jpg', b'esto no es una imagen'), 'El archivo no es una imagen válida.'),
            (archivo_imagen('animada.gif', 'GIF', (50, 50), 'RGB'), 'Solo se permiten imágenes JPG, PNG o WEBP.'),
            (SimpleUploadedFile('grande.jpg', b'0' * (3 * 1024 * 1024 + 1)), 'La imagen no puede pesar más de 3 MB.'),
        ]
        for archivo, mensaje in casos:
            with self.subTest(archivo=archivo.name):
                respuesta = self.subir(archivo)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.data['imagen'][0], mensaje)
        self.assertEqual(self.cliente.post(self.url, {}, format='multipart').status_code, 400)

    def test_maximo_de_imagenes(self):
        for orden in range(10):
            ImagenPublicacion.objects.create(publicacion=self.publicacion, contenido=b'x', orden=orden)
        self.cliente.force_login(self.anfitrion)
        respuesta = self.subir(archivo_imagen())
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('máximo de 10', respuesta.data['imagen'][0])

    def test_solo_el_dueno_sube_y_elimina(self):
        self.cliente.force_login(self.anfitrion)
        imagen_id = self.subir(archivo_imagen()).data['imagen']['id']
        url = reverse('imagen', args=[self.publicacion.pk, imagen_id])
        self.cliente.force_login(self.otro)
        self.assertEqual(self.subir(archivo_imagen()).status_code, 403)
        self.assertEqual(self.cliente.delete(url).status_code, 403)
        self.cliente.logout()
        self.assertEqual(self.subir(archivo_imagen()).status_code, 401)
        self.cliente.force_login(self.anfitrion)
        self.assertEqual(self.cliente.delete(url).status_code, 200)
        self.assertFalse(ImagenPublicacion.objects.exists())
