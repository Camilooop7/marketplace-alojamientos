import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from aplicaciones.publicacion.models import Publicacion


def dinero(**extra):
    return models.DecimalField(max_digits=12, decimal_places=2, **extra)


class Reserva(models.Model):

    class Estado(models.TextChoices):
        PENDIENTE_PAGO = 'PENDIENTE_PAGO', 'Pendiente de pago'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        CANCELADA = 'CANCELADA', 'Cancelada'
        COMPLETADA = 'COMPLETADA', 'Completada'

    ESTADOS_ACTIVOS = [Estado.PENDIENTE_PAGO, Estado.CONFIRMADA]

    codigo = models.CharField(max_length=12, unique=True, editable=False)
    huesped = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reservas')
    publicacion = models.ForeignKey(Publicacion, on_delete=models.PROTECT, related_name='reservas')
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()
    huespedes = models.PositiveSmallIntegerField()
    noches = models.PositiveSmallIntegerField()
    precio_noche = dinero()
    precio_base = dinero()
    descuento = dinero(default=0)
    tarifa_limpieza = dinero(default=0)
    total_servicios = dinero(default=0)
    servicios = models.JSONField(default=list, blank=True)
    total = dinero()
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE_PAGO)
    clave_idempotencia = models.CharField(max_length=64, blank=True)
    motivo_cancelacion = models.CharField(max_length=255, blank=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']
        constraints = [
            models.CheckConstraint(condition=Q(fecha_salida__gt=models.F('fecha_entrada')),
                                   name='reserva_salida_posterior_entrada'),
            models.UniqueConstraint(fields=['huesped', 'clave_idempotencia'],
                                    condition=~Q(clave_idempotencia=''),
                                    name='reserva_clave_idempotencia_unica'),
        ]

    def __str__(self):
        return '{0} - {1} ({2})'.format(self.codigo, self.publicacion.titulo, self.estado)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        super().save(*args, **kwargs)

    @staticmethod
    def generar_codigo():
        while True:
            codigo = 'RES-' + secrets.token_hex(4).upper()
            if not Reserva.objects.filter(codigo=codigo).exists():
                return codigo

    @classmethod
    def activas_en(cls, publicacion, entrada, salida):
        return cls.objects.filter(publicacion=publicacion, estado__in=cls.ESTADOS_ACTIVOS,
                                  fecha_entrada__lt=salida, fecha_salida__gt=entrada)

    @classmethod
    def futuras_de(cls, usuario):
        return cls.objects.filter(
            Q(huesped=usuario) | Q(publicacion__anfitrion=usuario),
            estado__in=cls.ESTADOS_ACTIVOS, fecha_salida__gte=timezone.localdate())

    def cambiar_estado(self, nuevo, usuario, detalle=''):
        anterior = self.estado
        self.estado = nuevo
        self.save()
        HistorialReserva.objects.create(reserva=self, estado_anterior=anterior, estado_nuevo=nuevo,
                                        usuario=usuario, detalle=detalle[:255])


class HistorialReserva(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=15, blank=True)
    estado_nuevo = models.CharField(max_length=15)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    detalle = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Historial de reservas'
        ordering = ['fecha', 'id']


class Factura(models.Model):

    class Estado(models.TextChoices):
        EMITIDA = 'EMITIDA', 'Emitida - pendiente de pago'
        ANULADA = 'ANULADA', 'Anulada'

    reserva = models.OneToOneField(Reserva, on_delete=models.PROTECT, related_name='factura')
    numero = models.CharField(max_length=20, unique=True, blank=True)
    cliente_nombre = models.CharField(max_length=301)
    cliente_correo = models.EmailField(max_length=120)
    total = dinero()
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.EMITIDA)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_generacion']

    def __str__(self):
        return '{0} ({1})'.format(self.numero, self.estado)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.numero:
            self.numero = 'FAC-{0}-{1:06d}'.format(self.fecha_generacion.year, self.pk)
            super().save(update_fields=['numero'])

    def contrato(self):
        return {
            'numero': self.numero,
            'reserva_id': self.reserva_id,
            'reserva_codigo': self.reserva.codigo,
            'cliente': {'id': self.reserva.huesped_id, 'nombre': self.cliente_nombre,
                        'correo': self.cliente_correo},
            'total': str(self.total),
            'moneda': 'COP',
            'fecha_generacion': self.fecha_generacion.isoformat(),
            'estado': self.estado,
            'pdf': reverse('factura_pdf', args=[self.reserva_id]),
        }
