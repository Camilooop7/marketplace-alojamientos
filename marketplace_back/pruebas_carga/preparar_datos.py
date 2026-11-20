import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

if not os.environ.get('DATABASE_URL', '').startswith('sqlite'):
    sys.exit('Define DATABASE_URL con una base SQLite local antes de preparar los datos de carga.')

import django

django.setup()

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.utils import timezone

from aplicaciones.gestion_usuario.models import Usuario
from aplicaciones.publicacion.models import Disponibilidad, Publicacion, ServicioAdicional

CLAVE = 'CargaLocal2026!'
HUESPEDES = 60
ALOJAMIENTOS = [
    ('Cabaña en el bosque', 'Guatapé', 'CABANA', 4, 200000),
    ('Apartamento en El Poblado', 'Medellín', 'APARTAMENTO', 5, 320000),
    ('Casa colonial', 'Villa de Leyva', 'CASA', 6, 480000),
    ('Habitación frente al mar', 'Santa Marta', 'HABITACION', 2, 210000),
    ('Dúplex en Chapinero', 'Bogotá', 'APARTAMENTO', 4, 260000),
    ('Casa campestre con piscina', 'Anapoima', 'CASA', 7, 650000),
    ('Habitación ejecutiva', 'Cali', 'HABITACION', 2, 150000),
    ('Cabaña con chimenea', 'Paipa', 'CABANA', 2, 300000),
    ('Habitación en Usaquén', 'Bogotá', 'HABITACION', 2, 180000),
    ('Apartamento en Cartagena', 'Cartagena', 'APARTAMENTO', 4, 390000),
]


def crear_usuario(nombre, rol):
    usuario = Usuario.objects.create_user(username=nombre, email='{0}@carga.test'.format(nombre), password=CLAVE,
                                          first_name='Prueba', last_name=nombre, correo_verificado=True)
    usuario.groups.add(Group.objects.get(name=rol))
    return usuario


call_command('migrate', verbosity=0)
if Usuario.objects.filter(username='anfitrion.carga').exists():
    sys.exit('Los datos de carga ya existen.')

anfitrion = crear_usuario('anfitrion.carga', Usuario.ROL_ANFITRION)
for numero in range(1, HUESPEDES + 1):
    crear_usuario('huesped{0:02d}'.format(numero), Usuario.ROL_HUESPED)

hoy = timezone.localdate()
for titulo, ciudad, tipo, capacidad, precio in ALOJAMIENTOS:
    publicacion = Publicacion.objects.create(
        anfitrion=anfitrion, titulo=titulo, descripcion='Alojamiento de prueba para la carga.', ciudad=ciudad,
        direccion='Dirección de prueba', tipo=tipo, capacidad=capacidad, precio_noche=precio,
        tarifa_limpieza=40000, estado=Publicacion.Estado.ACTIVA)
    Disponibilidad.objects.create(publicacion=publicacion, fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=365))
    ServicioAdicional.objects.create(publicacion=publicacion, nombre='Desayuno', precio=30000)

print('Listo: 1 anfitrión, {0} huéspedes y {1} alojamientos.'.format(HUESPEDES, len(ALOJAMIENTOS)))
