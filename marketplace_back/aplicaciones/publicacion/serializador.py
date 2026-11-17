from rest_framework import serializers

from .models import Disponibilidad, ImagenPublicacion, Publicacion, ServicioAdicional


class ServicioSerializador(serializers.ModelSerializer):

    class Meta:
        model = ServicioAdicional
        fields = ['id', 'nombre', 'precio']


class ImagenSerializador(serializers.ModelSerializer):

    class Meta:
        model = ImagenPublicacion
        fields = ['id', 'orden']


class PublicacionSerializador(serializers.ModelSerializer):
    anfitrion = serializers.CharField(source='anfitrion.get_full_name', read_only=True)
    anfitrion_id = serializers.IntegerField(read_only=True)
    servicios = ServicioSerializador(many=True, read_only=True)
    imagenes = ImagenSerializador(many=True, read_only=True)

    class Meta:
        model = Publicacion
        fields = ['id', 'anfitrion', 'anfitrion_id', 'titulo', 'descripcion', 'ciudad', 'direccion', 'tipo',
                  'capacidad', 'precio_noche', 'tarifa_limpieza', 'descuento_porcentaje',
                  'noches_descuento', 'estado', 'servicios', 'imagenes', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = fields


class DisponibilidadSerializador(serializers.ModelSerializer):

    class Meta:
        model = Disponibilidad
        fields = ['id', 'fecha_inicio', 'fecha_fin']
        read_only_fields = fields
