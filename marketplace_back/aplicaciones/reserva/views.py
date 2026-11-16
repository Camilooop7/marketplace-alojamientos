from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from aplicaciones.gestion_usuario.models import Auditoria
from aplicaciones.gestion_usuario.seguridad import SoloAnfitrion
from aplicaciones.publicacion.models import Publicacion
from aplicaciones.publicacion.views import obtener_visible
from .calculo import calcular_cotizacion, estancia_iniciada
from .factura import generar_pdf
from .models import Factura, Reserva
from .serializador import (
    CancelacionSerializador, ReservaDetalleSerializador, ReservaSerializador, SolicitudReservaSerializador,
)


def recurso_reserva(reserva):
    return 'Reserva {0}'.format(reserva.codigo)


def obtener_reserva(request, pk):
    reserva = get_object_or_404(Reserva.objects.select_related('publicacion__anfitrion', 'huesped'), pk=pk)
    usuario = request.user
    if usuario.pk not in (reserva.huesped_id, reserva.publicacion.anfitrion_id) and not usuario.es_administrador():
        raise NotFound('No encontramos esa reserva.')
    return reserva


def filtrar_estado(consulta, request):
    estado = request.query_params.get('estado', '')
    if estado in Reserva.Estado.values:
        consulta = consulta.filter(estado=estado)
    return consulta


def cotizacion_json(cotizacion):
    return {clave: str(valor) if not isinstance(valor, (int, list)) else valor
            for clave, valor in cotizacion.items()}


def crear_reserva(usuario, datos):
    clave = datos.get('clave_idempotencia', '')
    with transaction.atomic():
        publicacion = Publicacion.objects.select_for_update().get(pk=datos['publicacion'].pk)
        if clave:
            existente = Reserva.objects.filter(huesped=usuario, clave_idempotencia=clave).first()
            if existente:
                return existente, False
        if publicacion.estado != Publicacion.Estado.ACTIVA or Reserva.activas_en(
                publicacion, datos['fecha_entrada'], datos['fecha_salida']).exists():
            return None, False
        cotizacion = calcular_cotizacion(publicacion, datos['fecha_entrada'], datos['fecha_salida'],
                                         datos['servicios'])
        reserva = Reserva.objects.create(
            huesped=usuario, publicacion=publicacion, fecha_entrada=datos['fecha_entrada'],
            fecha_salida=datos['fecha_salida'], huespedes=datos['huespedes'],
            clave_idempotencia=clave, **cotizacion)
        reserva.historial.create(estado_nuevo=reserva.estado, usuario=usuario,
                                 detalle='Reserva creada, pendiente de pago')
        factura = Factura.objects.create(
            reserva=reserva, cliente_nombre=usuario.get_full_name() or usuario.username,
            cliente_correo=usuario.email, total=reserva.total)
    Auditoria.registrar(usuario, Auditoria.Accion.RESERVA, recurso_reserva(reserva),
                        'Reservó {0} del {1} al {2} por {3}'.format(
                            publicacion.titulo, reserva.fecha_entrada, reserva.fecha_salida, reserva.total))
    Auditoria.registrar(usuario, Auditoria.Accion.FACTURA, 'Factura {0}'.format(factura.numero),
                        'Factura generada para la reserva {0}'.format(reserva.codigo))
    return reserva, True


class CotizacionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializador = SolicitudReservaSerializador(data=request.data, context={'request': request})
        serializador.is_valid(raise_exception=True)
        datos = serializador.validated_data
        cotizacion = calcular_cotizacion(datos['publicacion'], datos['fecha_entrada'],
                                         datos['fecha_salida'], datos['servicios'])
        return Response(cotizacion_json(cotizacion))


class ReservaListaView(APIView):
    def get(self, request):
        consulta = filtrar_estado(
            Reserva.objects.filter(huesped=request.user).select_related('publicacion', 'huesped', 'factura'),
            request)
        return Response(ReservaSerializador(consulta, many=True).data)

    def post(self, request):
        clave = str(request.data.get('clave_idempotencia') or '')
        existente = clave and Reserva.objects.filter(huesped=request.user, clave_idempotencia=clave).first()
        if existente:
            return Response({'mensaje': 'Esta solicitud ya había sido registrada.',
                             'reserva': ReservaDetalleSerializador(existente).data})
        serializador = SolicitudReservaSerializador(
            data=request.data, context={'request': request, 'reservando': True})
        serializador.is_valid(raise_exception=True)
        reserva, creada = crear_reserva(request.user, serializador.validated_data)
        if reserva is None:
            Auditoria.registrar(request.user, Auditoria.Accion.RESERVA,
                                'Publicación #{0}'.format(serializador.validated_data['publicacion'].pk),
                                'Fechas ocupadas al confirmar', Auditoria.Resultado.RECHAZADO)
            return Response({'mensaje': 'Esas fechas acaban de ser reservadas por otra persona. '
                                        'Elige otras fechas.'}, status=status.HTTP_409_CONFLICT)
        mensaje = ('Reserva creada. Descarga tu factura y realiza el pago para confirmarla.' if creada
                   else 'Esta solicitud ya había sido registrada.')
        return Response({'mensaje': mensaje, 'reserva': ReservaDetalleSerializador(reserva).data},
                        status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK)


class ReservasRecibidasView(APIView):
    permission_classes = [SoloAnfitrion]

    def get(self, request):
        consulta = filtrar_estado(Reserva.objects.filter(publicacion__anfitrion=request.user)
                                  .select_related('publicacion', 'huesped', 'factura'), request)
        desde = parse_date(request.query_params.get('desde', '') or '')
        hasta = parse_date(request.query_params.get('hasta', '') or '')
        if desde:
            consulta = consulta.filter(fecha_salida__gt=desde)
        if hasta:
            consulta = consulta.filter(fecha_entrada__lt=hasta)
        return Response(ReservaSerializador(consulta, many=True).data)


class ReservaDetalleView(APIView):
    def get(self, request, pk):
        return Response(ReservaDetalleSerializador(obtener_reserva(request, pk)).data)


class CancelacionView(APIView):
    def revisar(self, request, pk):
        reserva = obtener_reserva(request, pk)
        if reserva.huesped_id != request.user.pk:
            return reserva, Response({'mensaje': 'Solo el huésped puede cancelar su reserva.'},
                                     status=status.HTTP_403_FORBIDDEN)
        if reserva.estado not in Reserva.ESTADOS_ACTIVOS or estancia_iniciada(reserva.fecha_entrada):
            return reserva, Response({'mensaje': 'Esta reserva ya no se puede cancelar.'},
                                     status=status.HTTP_409_CONFLICT)
        return reserva, None

    def post(self, request, pk):
        serializador = CancelacionSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        with transaction.atomic():
            Reserva.objects.select_for_update().filter(pk=pk).first()
            reserva, error = self.revisar(request, pk)
            if error:
                return error
            motivo = serializador.validated_data['motivo']
            reserva.motivo_cancelacion = motivo
            reserva.fecha_cancelacion = timezone.now()
            reserva.cambiar_estado(Reserva.Estado.CANCELADA, request.user, 'Motivo: {0}'.format(motivo))
            Factura.objects.filter(reserva=reserva).update(estado=Factura.Estado.ANULADA)
        Auditoria.registrar(request.user, Auditoria.Accion.CANCELACION, recurso_reserva(reserva),
                            'Canceló la reserva. Motivo: {0}'.format(motivo))
        return Response({'mensaje': 'Reserva cancelada. Las fechas quedaron libres.',
                         'reserva': ReservaDetalleSerializador(reserva).data})


class FacturaView(APIView):
    def get(self, request, pk):
        reserva = obtener_reserva(request, pk)
        return Response(reserva.factura.contrato())


class FacturaPdfView(APIView):
    def get(self, request, pk):
        factura = obtener_reserva(request, pk).factura
        respuesta = HttpResponse(generar_pdf(factura), content_type='application/pdf')
        respuesta['Content-Disposition'] = 'attachment; filename="{0}.pdf"'.format(factura.numero)
        return respuesta


class CalendarioView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        publicacion = obtener_visible(request, pk)
        ocupadas = Reserva.objects.filter(
            publicacion=publicacion, estado__in=Reserva.ESTADOS_ACTIVOS,
            fecha_salida__gt=timezone.localdate()).order_by('fecha_entrada')
        return Response({
            'disponibles': [{'inicio': p.fecha_inicio, 'fin': p.fecha_fin}
                            for p in publicacion.disponibilidades.filter(fecha_fin__gt=timezone.localdate())],
            'reservadas': [{'inicio': r.fecha_entrada, 'fin': r.fecha_salida} for r in ocupadas],
        })
