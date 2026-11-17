from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from aplicaciones.gestion_usuario.seguridad import SoloAnfitrion
from .models import ImagenPublicacion, Publicacion
from .serializador import DisponibilidadSerializador, ImagenSerializador, PublicacionSerializador


def con_relaciones(consulta):
    return consulta.prefetch_related(
        'servicios', Prefetch('imagenes', queryset=ImagenPublicacion.objects.defer('contenido')))


def puede_ver_oculta(usuario, publicacion):
    return usuario.is_authenticated and (
        publicacion.anfitrion_id == usuario.pk or usuario.es_administrador())


def obtener_visible(request, pk):
    publicacion = get_object_or_404(con_relaciones(Publicacion.objects.all()), pk=pk)
    if publicacion.estado != Publicacion.Estado.ACTIVA and not puede_ver_oculta(request.user, publicacion):
        raise NotFound('Esta publicación no está disponible.')
    return publicacion


class PublicacionListaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        consulta = con_relaciones(Publicacion.objects.filter(estado=Publicacion.Estado.ACTIVA))
        ciudad = request.query_params.get('ciudad', '').strip()
        if ciudad:
            consulta = consulta.filter(ciudad__icontains=ciudad)
        huespedes = request.query_params.get('huespedes', '')
        if huespedes.isdigit():
            consulta = consulta.filter(capacidad__gte=int(huespedes))
        tipo = request.query_params.get('tipo', '')
        if tipo in Publicacion.Tipo.values:
            consulta = consulta.filter(tipo=tipo)
        return Response(PublicacionSerializador(consulta, many=True).data)


class MisPublicacionesView(ListAPIView):
    permission_classes = [SoloAnfitrion]
    serializer_class = PublicacionSerializador

    def get_queryset(self):
        return con_relaciones(Publicacion.objects.filter(anfitrion=self.request.user))


class PublicacionDetalleView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        return Response(PublicacionSerializador(obtener_visible(request, pk)).data)


class DisponibilidadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        publicacion = obtener_visible(request, pk)
        return Response(DisponibilidadSerializador(publicacion.disponibilidades.all(), many=True).data)


class ImagenesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        publicacion = obtener_visible(request, pk)
        return Response(ImagenSerializador(publicacion.imagenes.all(), many=True).data)


class ImagenArchivoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk, imagen_id):
        publicacion = obtener_visible(request, pk)
        imagen = get_object_or_404(ImagenPublicacion, pk=imagen_id, publicacion=publicacion)
        respuesta = HttpResponse(bytes(imagen.contenido), content_type=imagen.tipo_contenido)
        respuesta['Cache-Control'] = 'public, max-age=86400' if publicacion.estado == Publicacion.Estado.ACTIVA \
            else 'private, max-age=300'
        return respuesta
