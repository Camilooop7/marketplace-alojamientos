from django.db.models import Max, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from aplicaciones.gestion_usuario.models import Auditoria
from aplicaciones.gestion_usuario.seguridad import CuentaHabilitada, SoloAnfitrion
from .models import Disponibilidad, ImagenPublicacion, Publicacion
from .serializador import (CAMPOS_AUDITADOS, DisponibilidadSerializador, ImagenSerializador,
                           PublicacionSerializador, SubirImagenSerializador)


def con_relaciones(consulta):
    return consulta.prefetch_related(
        'servicios', Prefetch('imagenes', queryset=ImagenPublicacion.objects.defer('contenido')))


def recurso_publicacion(publicacion):
    return 'Publicación #{0}'.format(publicacion.pk)


def puede_gestionar(usuario, publicacion):
    return usuario.is_authenticated and (
        publicacion.anfitrion_id == usuario.pk or usuario.es_administrador())


def obtener_visible(request, pk):
    publicacion = get_object_or_404(con_relaciones(Publicacion.objects.all()), pk=pk)
    if publicacion.estado != Publicacion.Estado.ACTIVA and not puede_gestionar(request.user, publicacion):
        raise NotFound('Esta publicación no está disponible.')
    return publicacion


def obtener_gestionable(request, pk):
    publicacion = obtener_visible(request, pk)
    if not puede_gestionar(request.user, publicacion):
        raise PermissionDenied('Solo el anfitrión dueño o un administrador puede modificar esta publicación.')
    if publicacion.estado == Publicacion.Estado.BLOQUEADA and not request.user.es_administrador():
        raise PermissionDenied('La publicación fue bloqueada por un administrador y no se puede modificar.')
    return publicacion


class PublicacionListaView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [SoloAnfitrion()]

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
        return Response(PublicacionSerializador(consulta, many=True, context={'request': request}).data)

    def post(self, request):
        serializador = PublicacionSerializador(data=request.data, context={'request': request})
        serializador.is_valid(raise_exception=True)
        publicacion = serializador.save()
        Auditoria.registrar(request.user, Auditoria.Accion.PUBLICACION, recurso_publicacion(publicacion),
                            'Creó la publicación "{0}"'.format(publicacion.titulo))
        return Response({'mensaje': 'Publicación creada.', 'publicacion': serializador.data},
                        status=status.HTTP_201_CREATED)


class MisPublicacionesView(ListAPIView):
    permission_classes = [SoloAnfitrion]
    serializer_class = PublicacionSerializador

    def get_queryset(self):
        return con_relaciones(Publicacion.objects.filter(anfitrion=self.request.user))


class PublicacionDetalleView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [CuentaHabilitada()]

    def get(self, request, pk):
        publicacion = obtener_visible(request, pk)
        return Response(PublicacionSerializador(publicacion, context={'request': request}).data)

    def put(self, request, pk):
        publicacion = obtener_gestionable(request, pk)
        anteriores = {campo: getattr(publicacion, campo) for campo in CAMPOS_AUDITADOS}
        serializador = PublicacionSerializador(
            publicacion, data=request.data, partial=True, context={'request': request})
        serializador.is_valid(raise_exception=True)
        serializador.save()
        cambios = ['{0}: {1} -> {2}'.format(campo, valor, getattr(publicacion, campo))
                   for campo, valor in anteriores.items() if getattr(publicacion, campo) != valor]
        Auditoria.registrar(request.user, Auditoria.Accion.PUBLICACION, recurso_publicacion(publicacion),
                            'Editó la publicación. ' + ('; '.join(cambios) or 'Sin cambios en tarifas ni estado'))
        return Response({'mensaje': 'Publicación actualizada.', 'publicacion': serializador.data})


class DisponibilidadView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [CuentaHabilitada()]

    def get(self, request, pk):
        publicacion = obtener_visible(request, pk)
        return Response(DisponibilidadSerializador(publicacion.disponibilidades.all(), many=True).data)

    def post(self, request, pk):
        publicacion = obtener_gestionable(request, pk)
        serializador = DisponibilidadSerializador(data=request.data, context={'publicacion': publicacion})
        serializador.is_valid(raise_exception=True)
        periodo = serializador.save(publicacion=publicacion)
        Auditoria.registrar(request.user, Auditoria.Accion.PUBLICACION, recurso_publicacion(publicacion),
                            'Agregó disponibilidad del {0}'.format(periodo))
        return Response({'mensaje': 'Periodo disponible agregado.', 'periodo': serializador.data},
                        status=status.HTTP_201_CREATED)


class DisponibilidadDetalleView(APIView):
    permission_classes = [CuentaHabilitada]

    def delete(self, request, pk, periodo_id):
        from aplicaciones.reserva.models import Reserva

        publicacion = obtener_gestionable(request, pk)
        periodo = get_object_or_404(Disponibilidad, pk=periodo_id, publicacion=publicacion)
        if Reserva.activas_en(publicacion, periodo.fecha_inicio, periodo.fecha_fin).exists():
            return Response({'mensaje': 'No puedes eliminar un periodo que tiene reservas activas.'},
                            status=status.HTTP_409_CONFLICT)
        periodo.delete()
        Auditoria.registrar(request.user, Auditoria.Accion.PUBLICACION, recurso_publicacion(publicacion),
                            'Eliminó disponibilidad del {0}'.format(periodo))
        return Response({'mensaje': 'Periodo eliminado.'})


class ImagenesView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [CuentaHabilitada()]

    def get(self, request, pk):
        publicacion = obtener_visible(request, pk)
        return Response(ImagenSerializador(publicacion.imagenes.all(), many=True).data)

    def post(self, request, pk):
        publicacion = obtener_gestionable(request, pk)
        serializador = SubirImagenSerializador(data=request.data, context={'publicacion': publicacion})
        serializador.is_valid(raise_exception=True)
        ultimo = publicacion.imagenes.aggregate(ultimo=Max('orden'))['ultimo']
        imagen = ImagenPublicacion.objects.create(
            publicacion=publicacion, contenido=serializador.validated_data['imagen'],
            orden=0 if ultimo is None else ultimo + 1)
        Auditoria.registrar(request.user, Auditoria.Accion.PUBLICACION, recurso_publicacion(publicacion),
                            'Agregó la imagen #{0}'.format(imagen.pk))
        return Response({'mensaje': 'Imagen agregada.', 'imagen': ImagenSerializador(imagen).data},
                        status=status.HTTP_201_CREATED)


class ImagenDetalleView(APIView):
    permission_classes = [CuentaHabilitada]

    def delete(self, request, pk, imagen_id):
        publicacion = obtener_gestionable(request, pk)
        imagen = get_object_or_404(ImagenPublicacion.objects.defer('contenido'), pk=imagen_id,
                                   publicacion=publicacion)
        imagen.delete()
        Auditoria.registrar(request.user, Auditoria.Accion.PUBLICACION, recurso_publicacion(publicacion),
                            'Eliminó la imagen #{0}'.format(imagen_id))
        return Response({'mensaje': 'Imagen eliminada.'})


class ImagenArchivoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk, imagen_id):
        publicacion = obtener_visible(request, pk)
        imagen = get_object_or_404(ImagenPublicacion, pk=imagen_id, publicacion=publicacion)
        respuesta = HttpResponse(bytes(imagen.contenido), content_type=imagen.tipo_contenido)
        respuesta['Cache-Control'] = 'public, max-age=86400' if publicacion.estado == Publicacion.Estado.ACTIVA             else 'private, max-age=300'
        return respuesta
