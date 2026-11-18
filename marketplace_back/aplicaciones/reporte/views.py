from datetime import date, datetime
from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from aplicaciones.gestion_usuario.seguridad import SoloAdministrador, SoloAnfitrion
from .pdf import pdf_anfitrion, pdf_general
from .resumen import anfitriones, reporte_anfitrion, reporte_general


def leer_fecha(request, campo, nombre_campo):
    valor = request.query_params.get(campo, '')
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ValidationError({'mensaje': 'La fecha {0} no es válida.'.format(nombre_campo)})


def leer_periodo(request):
    desde = leer_fecha(request, 'desde', 'inicial')
    hasta = leer_fecha(request, 'hasta', 'final')
    if desde and hasta and desde > hasta:
        raise ValidationError({'mensaje': 'La fecha inicial no puede ser posterior a la final.'})
    return desde, hasta


def a_json(valor):
    if isinstance(valor, dict):
        return {clave: a_json(dato) for clave, dato in valor.items()}
    if isinstance(valor, list):
        return [a_json(dato) for dato in valor]
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, datetime):
        return timezone.localtime(valor).isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def respuesta_pdf(contenido, archivo):
    respuesta = HttpResponse(contenido, content_type='application/pdf')
    respuesta['Content-Disposition'] = 'attachment; filename="{0}.pdf"'.format(archivo)
    return respuesta


def sufijo(desde, hasta):
    return ''.join('-{0}'.format(fecha.isoformat()) for fecha in (desde, hasta) if fecha)


def obtener_anfitrion(pk):
    anfitrion = anfitriones().filter(pk=pk).first()
    if anfitrion is None:
        raise NotFound('No encontramos ese anfitrión.')
    return anfitrion


class MiReporteView(APIView):
    permission_classes = [SoloAnfitrion]

    def get(self, request):
        return Response(a_json(reporte_anfitrion(request.user, *leer_periodo(request))))


class MiReportePdfView(APIView):
    permission_classes = [SoloAnfitrion]

    def get(self, request):
        desde, hasta = leer_periodo(request)
        reporte = reporte_anfitrion(request.user, desde, hasta)
        return respuesta_pdf(pdf_anfitrion(reporte), 'reporte-{0}{1}'.format(request.user.username,
                                                                          sufijo(desde, hasta)))


class ReporteGeneralView(APIView):
    permission_classes = [SoloAdministrador]

    def get(self, request):
        return Response(a_json(reporte_general(*leer_periodo(request))))


class ReporteGeneralPdfView(APIView):
    permission_classes = [SoloAdministrador]

    def get(self, request):
        desde, hasta = leer_periodo(request)
        return respuesta_pdf(pdf_general(reporte_general(desde, hasta)),
                             'reporte-anfitriones{0}'.format(sufijo(desde, hasta)))


class ReporteAnfitrionView(APIView):
    permission_classes = [SoloAdministrador]

    def get(self, request, pk):
        return Response(a_json(reporte_anfitrion(obtener_anfitrion(pk), *leer_periodo(request))))


class ReporteAnfitrionPdfView(APIView):
    permission_classes = [SoloAdministrador]

    def get(self, request, pk):
        anfitrion = obtener_anfitrion(pk)
        desde, hasta = leer_periodo(request)
        return respuesta_pdf(pdf_anfitrion(reporte_anfitrion(anfitrion, desde, hasta)),
                             'reporte-{0}{1}'.format(anfitrion.username, sufijo(desde, hasta)))
