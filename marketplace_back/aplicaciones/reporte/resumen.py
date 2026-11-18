from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.utils import timezone

from aplicaciones.gestion_usuario.models import Usuario
from aplicaciones.publicacion.models import Publicacion
from aplicaciones.reserva.models import Reserva

CERO = Decimal('0')
COBRADAS = (Reserva.Estado.CONFIRMADA, Reserva.Estado.COMPLETADA)
MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def nombre(usuario):
    return usuario.get_full_name() or usuario.username


def datos_anfitrion(usuario):
    return {'id': usuario.pk, 'nombre': nombre(usuario), 'usuario': usuario.username, 'correo': usuario.email}


def consultar_reservas(desde=None, hasta=None, **filtros):
    consulta = (Reserva.objects.filter(**filtros)
                .select_related('publicacion__anfitrion', 'huesped').order_by('fecha_entrada', 'id'))
    if desde:
        consulta = consulta.filter(fecha_entrada__gte=desde)
    if hasta:
        consulta = consulta.filter(fecha_entrada__lte=hasta)
    return list(consulta)


def vigentes(reservas):
    return [reserva for reserva in reservas if reserva.estado != Reserva.Estado.CANCELADA]


def sumar(reservas, campo):
    return sum((getattr(reserva, campo) for reserva in reservas), CERO if campo == 'total' else 0)


def calcular_totales(reservas):
    validas = vigentes(reservas)
    ingresos = sumar(validas, 'total')
    confirmados = sumar([reserva for reserva in validas if reserva.estado in COBRADAS], 'total')
    noches = sumar(validas, 'noches')
    canceladas = len(reservas) - len(validas)
    return {
        'reservas': len(reservas),
        'reservas_vigentes': len(validas),
        'canceladas': canceladas,
        'ingresos': ingresos,
        'ingresos_confirmados': confirmados,
        'ingresos_pendientes': ingresos - confirmados,
        'noches': noches,
        'huespedes': sumar(validas, 'huespedes'),
        'clientes': len({reserva.huesped_id for reserva in validas}),
    }


def contar_estados(reservas):
    conteo = {estado: 0 for estado in Reserva.Estado.values}
    for reserva in reservas:
        conteo[reserva.estado] += 1
    return [{'estado': estado, 'etiqueta': Reserva.Estado(estado).label, 'cantidad': cantidad}
            for estado, cantidad in conteo.items()]


def agrupar(reservas, clave):
    grupos = defaultdict(list)
    for reserva in reservas:
        grupos[clave(reserva)].append(reserva)
    return grupos


def metricas(reservas):
    validas = vigentes(reservas)
    return {'reservas': len(validas), 'canceladas': len(reservas) - len(validas),
            'noches': sumar(validas, 'noches'), 'huespedes': sumar(validas, 'huespedes'),
            'ingresos': sumar(validas, 'total')}


def siguiente_mes(dia):
    return date(dia.year + dia.month // 12, dia.month % 12 + 1, 1)


def por_mes(reservas):
    if not reservas:
        return []
    grupos = agrupar(reservas, lambda reserva: reserva.fecha_entrada.replace(day=1))
    mes, ultimo = min(grupos), max(grupos)
    meses = []
    while mes <= ultimo:
        meses.append({'mes': mes.strftime('%Y-%m'),
                      'etiqueta': '{0} {1}'.format(MESES_CORTOS[mes.month - 1], mes.year),
                      **metricas(grupos.get(mes, []))})
        mes = siguiente_mes(mes)
    return meses


def por_alojamiento(publicaciones, reservas):
    grupos = agrupar(reservas, lambda reserva: reserva.publicacion_id)
    filas = [{'id': publicacion.pk, 'titulo': publicacion.titulo, 'ciudad': publicacion.ciudad,
              'tipo': publicacion.tipo, 'tipo_etiqueta': publicacion.get_tipo_display(),
              'estado': publicacion.estado, **metricas(grupos.get(publicacion.pk, []))}
             for publicacion in publicaciones]
    return sorted(filas, key=lambda fila: (-fila['ingresos'], -fila['reservas'], fila['titulo']))


def por_cliente(reservas):
    grupos = agrupar(reservas, lambda reserva: reserva.huesped)
    filas = []
    for huesped, grupo in grupos.items():
        datos = metricas(grupo)
        if datos['reservas']:
            filas.append({'id': huesped.pk, 'nombre': nombre(huesped), 'correo': huesped.email, **datos})
    return sorted(filas, key=lambda fila: (-fila['ingresos'], fila['nombre']))


def detalle_reservas(reservas):
    return [{'id': reserva.pk, 'codigo': reserva.codigo, 'huesped': nombre(reserva.huesped),
             'alojamiento': reserva.publicacion.titulo, 'tipo': reserva.publicacion.get_tipo_display(),
             'fecha_entrada': reserva.fecha_entrada, 'fecha_salida': reserva.fecha_salida,
             'noches': reserva.noches, 'huespedes': reserva.huespedes, 'total': reserva.total,
             'estado': reserva.estado}
            for reserva in sorted(reservas, key=lambda reserva: (reserva.fecha_entrada, reserva.pk), reverse=True)]


def periodo(desde, hasta):
    return {'desde': desde, 'hasta': hasta}


def reporte_anfitrion(anfitrion, desde=None, hasta=None):
    reservas = consultar_reservas(desde, hasta, publicacion__anfitrion=anfitrion)
    publicaciones = Publicacion.objects.filter(anfitrion=anfitrion).order_by('titulo')
    return {
        'anfitrion': datos_anfitrion(anfitrion),
        'periodo': periodo(desde, hasta),
        'generado': timezone.now(),
        'resumen': {**calcular_totales(reservas), 'alojamientos': publicaciones.count()},
        'estados': contar_estados(reservas),
        'meses': por_mes(reservas),
        'alojamientos': por_alojamiento(publicaciones, reservas),
        'clientes': por_cliente(reservas),
        'reservas': detalle_reservas(reservas),
    }


def anfitriones():
    return Usuario.objects.filter(groups__name=Usuario.ROL_ANFITRION).distinct().order_by(
        'first_name', 'last_name', 'username')


def reporte_general(desde=None, hasta=None):
    reservas = consultar_reservas(desde, hasta)
    grupos = agrupar(reservas, lambda reserva: reserva.publicacion.anfitrion_id)
    alojamientos = defaultdict(int)
    for anfitrion_id in Publicacion.objects.values_list('anfitrion_id', flat=True):
        alojamientos[anfitrion_id] += 1
    filas = [{**datos_anfitrion(anfitrion), 'alojamientos': alojamientos[anfitrion.pk],
              **calcular_totales(grupos.get(anfitrion.pk, []))} for anfitrion in anfitriones()]
    filas.sort(key=lambda fila: (-fila['ingresos'], -fila['reservas'], fila['nombre']))
    return {
        'periodo': periodo(desde, hasta),
        'generado': timezone.now(),
        'resumen': {**calcular_totales(reservas), 'anfitriones': len(filas),
                    'alojamientos': sum(alojamientos.values())},
        'estados': contar_estados(reservas),
        'meses': por_mes(reservas),
        'anfitriones': filas,
    }
