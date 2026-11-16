from django.db import transaction
from rest_framework import serializers

from aplicaciones.gestion_usuario.serializador import obligatorio
from aplicaciones.validacion import normalizar_espacios, validar_solo_letras, validar_texto_seguro
from .imagen import MAXIMO_IMAGENES, procesar_imagen
from .models import Disponibilidad, ImagenPublicacion, Publicacion, ServicioAdicional

ESTADOS_ANFITRION = [Publicacion.Estado.BORRADOR, Publicacion.Estado.ACTIVA, Publicacion.Estado.PAUSADA]
CAMPOS_AUDITADOS = ['titulo', 'ciudad', 'capacidad', 'precio_noche', 'tarifa_limpieza',
                    'descuento_porcentaje', 'noches_descuento', 'estado']


def mayor_que_cero(texto):
    return {**obligatorio(texto), 'invalid': texto, 'min_value': texto}


class ServicioSerializador(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=60, error_messages=obligatorio('Escribe el nombre del servicio.'))
    precio = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, error_messages={
        **obligatorio('Escribe el precio del servicio.'),
        'min_value': 'El precio del servicio no puede ser negativo.'})

    class Meta:
        model = ServicioAdicional
        fields = ['id', 'nombre', 'precio']

    def validate_nombre(self, valor):
        valor = normalizar_espacios(valor)
        validar_texto_seguro(valor, 'El nombre del servicio')
        return valor


class ImagenSerializador(serializers.ModelSerializer):

    class Meta:
        model = ImagenPublicacion
        fields = ['id', 'orden']


class SubirImagenSerializador(serializers.Serializer):
    imagen = serializers.FileField(error_messages={
        **obligatorio('Elige una imagen.'), 'invalid': 'El archivo no es una imagen válida.',
        'empty': 'El archivo está vacío.'})

    def validate_imagen(self, archivo):
        if self.context['publicacion'].imagenes.count() >= MAXIMO_IMAGENES:
            raise serializers.ValidationError(
                'La publicación ya tiene el máximo de {0} imágenes.'.format(MAXIMO_IMAGENES))
        return procesar_imagen(archivo)


class PublicacionSerializador(serializers.ModelSerializer):
    anfitrion = serializers.CharField(source='anfitrion.get_full_name', read_only=True)
    titulo = serializers.CharField(min_length=5, max_length=120, error_messages={
        **obligatorio('Escribe el título.'), 'min_length': 'El título debe tener al menos 5 caracteres.'})
    descripcion = serializers.CharField(min_length=20, max_length=2000, error_messages={
        **obligatorio('Escribe la descripción.'),
        'min_length': 'La descripción debe tener al menos 20 caracteres.'})
    ciudad = serializers.CharField(max_length=80, error_messages=obligatorio('Escribe la ciudad.'))
    direccion = serializers.CharField(max_length=150, error_messages=obligatorio('Escribe la dirección.'))
    capacidad = serializers.IntegerField(min_value=1, max_value=50, error_messages={
        **mayor_que_cero('La capacidad debe ser un número mayor que cero.'),
        'max_value': 'La capacidad máxima es de 50 huéspedes.'})
    precio_noche = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=1,
        error_messages=mayor_que_cero('El precio por noche debe ser mayor que cero.'))
    tarifa_limpieza = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False,
        error_messages={'min_value': 'La tarifa de limpieza no puede ser negativa.'})
    descuento_porcentaje = serializers.IntegerField(
        min_value=0, max_value=90, required=False,
        error_messages={'min_value': 'El descuento no puede ser negativo.',
                        'max_value': 'El descuento no puede ser mayor a 90.'})
    noches_descuento = serializers.IntegerField(
        min_value=1, required=False,
        error_messages={'min_value': 'Las noches para el descuento deben ser al menos 1.'})
    servicios = ServicioSerializador(many=True, required=False)
    imagenes = ImagenSerializador(many=True, read_only=True)

    class Meta:
        model = Publicacion
        fields = ['id', 'anfitrion', 'titulo', 'descripcion', 'ciudad', 'direccion', 'tipo',
                  'capacidad', 'precio_noche', 'tarifa_limpieza', 'descuento_porcentaje',
                  'noches_descuento', 'estado', 'servicios',
                  'imagenes', 'fecha_creacion', 'fecha_actualizacion']
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
        extra_kwargs = {
            'tipo': {'error_messages': {**obligatorio('Elige el tipo de alojamiento.'),
                                        'invalid_choice': 'El tipo de alojamiento no es válido.'}},
            'estado': {'error_messages': {'invalid_choice': 'El estado no es válido.'}},
        }

    def validate_titulo(self, valor):
        valor = normalizar_espacios(valor)
        validar_texto_seguro(valor, 'El título')
        return valor

    def validate_descripcion(self, valor):
        valor = valor.strip()
        if '<' in valor or '>' in valor:
            raise serializers.ValidationError('La descripción no puede contener los caracteres < o >.')
        return valor

    def validate_ciudad(self, valor):
        valor = normalizar_espacios(valor)
        validar_solo_letras(valor, 'La ciudad')
        return valor

    def validate_direccion(self, valor):
        valor = normalizar_espacios(valor)
        validar_texto_seguro(valor, 'La dirección')
        return valor

    def validate_estado(self, valor):
        usuario = self.context['request'].user
        if not usuario.es_administrador() and valor not in ESTADOS_ANFITRION:
            raise serializers.ValidationError(
                'Solo puedes dejar la publicación en borrador, activa o pausada.')
        return valor

    def validate_servicios(self, valor):
        nombres = [servicio['nombre'].lower() for servicio in valor]
        if len(nombres) != len(set(nombres)):
            raise serializers.ValidationError('Hay servicios con el mismo nombre.')
        return valor

    def guardar_servicios(self, publicacion, servicios):
        if servicios is None:
            return
        publicacion.servicios.all().delete()
        ServicioAdicional.objects.bulk_create(
            ServicioAdicional(publicacion=publicacion, **servicio) for servicio in servicios)

    def create(self, datos):
        servicios = datos.pop('servicios', [])
        with transaction.atomic():
            publicacion = Publicacion.objects.create(anfitrion=self.context['request'].user, **datos)
            self.guardar_servicios(publicacion, servicios)
        return publicacion

    def update(self, publicacion, datos):
        servicios = datos.pop('servicios', None)
        with transaction.atomic():
            publicacion = super().update(publicacion, datos)
            self.guardar_servicios(publicacion, servicios)
        return publicacion


class DisponibilidadSerializador(serializers.ModelSerializer):
    fecha_inicio = serializers.DateField(error_messages={
        **obligatorio('Escribe la fecha de inicio.'), 'invalid': 'La fecha de inicio no es válida.'})
    fecha_fin = serializers.DateField(error_messages={
        **obligatorio('Escribe la fecha de fin.'), 'invalid': 'La fecha de fin no es válida.'})

    class Meta:
        model = Disponibilidad
        fields = ['id', 'fecha_inicio', 'fecha_fin']

    def validate(self, datos):
        if datos['fecha_fin'] <= datos['fecha_inicio']:
            raise serializers.ValidationError(
                {'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'})
        cruce = Disponibilidad.objects.filter(
            publicacion=self.context['publicacion'],
            fecha_inicio__lt=datos['fecha_fin'], fecha_fin__gt=datos['fecha_inicio']).first()
        if cruce:
            raise serializers.ValidationError(
                {'fecha_inicio': 'El periodo se cruza con otro ya registrado: {0}.'.format(cruce)})
        return datos
