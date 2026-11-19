import itertools
import random
from datetime import date, timedelta

from locust import HttpUser, between, task

CLAVE = 'CargaLocal2026!'
HUESPEDES = itertools.cycle('huesped{0:02d}'.format(numero) for numero in range(1, 61))
ALOJAMIENTOS = range(1, 11)


def fechas():
    entrada = date.today() + timedelta(days=random.randint(5, 330))
    return entrada.isoformat(), (entrada + timedelta(days=random.randint(1, 4))).isoformat()


def solicitud():
    entrada, salida = fechas()
    return {'publicacion': random.choice(ALOJAMIENTOS), 'fecha_entrada': entrada, 'fecha_salida': salida,
            'huespedes': 2, 'servicios': []}


def aceptar_ocupadas(respuesta, esperado):
    if respuesta.status_code == esperado or (respuesta.status_code == 400 and 'reservado' in respuesta.text):
        respuesta.success()
    else:
        respuesta.failure('{0}: {1}'.format(respuesta.status_code, respuesta.text[:120]))


class UsuarioConSesion(HttpUser):
    abstract = True
    wait_time = between(1, 3)
    cuenta = None

    def on_start(self):
        self.client.get('/api/csrf/', name='/api/csrf/')
        self.client.post('/api/auth/ingresar/', json={'correo_o_usuario': self.cuenta or next(HUESPEDES),
                                                      'contrasena': CLAVE},
                         headers=self.encabezados(), name='/api/auth/ingresar/')

    def encabezados(self):
        return {'X-CSRFToken': self.client.cookies.get('csrftoken', ''), 'Referer': self.host}


class Huesped(UsuarioConSesion):
    weight = 4

    @task(4)
    def cotizar(self):
        with self.client.post('/api/reservas/cotizacion/', json=solicitud(), headers=self.encabezados(),
                              name='/api/reservas/cotizacion/', catch_response=True) as respuesta:
            aceptar_ocupadas(respuesta, 200)

    @task(2)
    def ver_calendario(self):
        self.client.get('/api/publicaciones/{0}/calendario/'.format(random.choice(ALOJAMIENTOS)),
                        name='/api/publicaciones/[id]/calendario/')

    @task(2)
    def mis_reservas(self):
        self.client.get('/api/reservas/', name='/api/reservas/ (consultar)')

    @task(1)
    def reservar(self):
        with self.client.post('/api/reservas/', json=solicitud(), headers=self.encabezados(),
                              name='/api/reservas/ (crear)', catch_response=True) as respuesta:
            aceptar_ocupadas(respuesta, 201)

    @task(1)
    def descargar_factura(self):
        reservas = self.client.get('/api/reservas/', name='/api/reservas/ (consultar)').json()
        if reservas:
            self.client.get('/api/reservas/{0}/factura/pdf/'.format(reservas[0]['id']),
                            name='/api/reservas/[id]/factura/pdf/')


class Anfitrion(UsuarioConSesion):
    weight = 1
    cuenta = 'anfitrion.carga'

    @task(3)
    def reservas_recibidas(self):
        self.client.get('/api/reservas/recibidas/', name='/api/reservas/recibidas/')

    @task(1)
    def detalle_reserva(self):
        recibidas = self.client.get('/api/reservas/recibidas/', params={'estado': 'PENDIENTE_PAGO'},
                                    name='/api/reservas/recibidas/').json()
        if recibidas:
            self.client.get('/api/reservas/{0}/'.format(random.choice(recibidas)['id']),
                            name='/api/reservas/[id]/')
