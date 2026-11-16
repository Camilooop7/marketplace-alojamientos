from datetime import datetime, time
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

CENTAVO = Decimal('0.01')


def redondear(valor):
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_cotizacion(publicacion, entrada, salida, servicios=(), porcentaje=None):
    if porcentaje is None:
        porcentaje = settings.TARIFA_SERVICIO_PORCENTAJE
    noches = (salida - entrada).days
    precio_base = redondear(publicacion.precio_noche * noches)
    descuento = Decimal('0')
    if publicacion.descuento_porcentaje and noches >= publicacion.noches_descuento:
        descuento = redondear(precio_base * publicacion.descuento_porcentaje / 100)
    total_servicios = redondear(sum((servicio.precio for servicio in servicios), Decimal('0')))
    limpieza = redondear(publicacion.tarifa_limpieza)
    subtotal = precio_base - descuento + limpieza + total_servicios
    tarifa_servicio = redondear(subtotal * Decimal(porcentaje) / 100)
    return {
        'noches': noches,
        'precio_noche': redondear(publicacion.precio_noche),
        'precio_base': precio_base,
        'descuento': redondear(descuento),
        'tarifa_limpieza': limpieza,
        'servicios': [{'nombre': s.nombre, 'precio': str(redondear(s.precio))} for s in servicios],
        'total_servicios': total_servicios,
        'subtotal': redondear(subtotal),
        'porcentaje_tarifa_servicio': redondear(porcentaje),
        'tarifa_servicio': tarifa_servicio,
        'total': redondear(subtotal + tarifa_servicio),
    }


def estancia_iniciada(entrada, ahora=None):
    ahora = ahora or timezone.now()
    return ahora >= timezone.make_aware(datetime.combine(entrada, time.min))
