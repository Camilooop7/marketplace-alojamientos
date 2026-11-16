from django.utils import timezone
from rest_framework import serializers

from aplicaciones.gestion_usuario.serializador import obligatorio
from aplicaciones.publicacion.models import Publicacion
from .models import HistorialReserva, Reserva


class SolicitudReservaSerializador(serializers.Serializer):
    publicacion = serializers.PrimaryKeyRelatedField(
        queryset=Publicacion.objects.all(), error_messages={
            **obligatorio('Elige el alojamiento.'),
            'does_not_exist': 'El alojamiento no existe.', 'incorrect_type': 'El alojamiento no es válido.'})
    fecha_entrada = serializers.DateField(error_messages={
        **obligatorio('Escribe la fecha de entrada.'), 'invalid': 'La fecha de entrada no es válida.'})
    fecha_salida = serializers.DateField(error_messages={
        **obligatorio('Escribe la fecha de salida.'), 'invalid': 'La fecha de salida no es válida.'})
    huespedes = serializers.IntegerField(min_value=1, error_messages={
        **obligatorio('Escribe el número de huéspedes.'), 'invalid': 'El número de huéspedes no es válido.',
        'min_value': 'Debe haber al menos un huésped.'})
    servicios = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    clave_idempotencia = serializers.RegexField(
        r'^[A-Za-z0-9-]{8,64}$', required=False, allow_blank=True,
        error_messages={'invalid': 'La clave de la solicitud no es válida.'})

    def validate(self, datos):
        publicacion = datos['publicacion']
        entrada, salida = datos['fecha_entrada'], datos['fecha_salida']
        usuario = self.context['request'].user
        if salida <= entrada:
            raise serializers.ValidationError(
                {'fecha_salida': 'La fecha de salida debe ser posterior a la de entrada.'})
        if entrada < timezone.localdate():
            raise serializers.ValidationError({'fecha_entrada': 'La fecha de entrada no puede ser pasada.'})
        if publicacion.estado != Publicacion.Estado.ACTIVA:
            raise serializers.ValidationError(
                {'publicacion': 'Este alojamiento no está disponible para reservar.'})
        if self.context.get('reservando') and publicacion.anfitrion_id == usuario.pk:
            raise serializers.ValidationError({'publicacion': 'No puedes reservar tu propia publicación.'})
        if datos['huespedes'] > publicacion.capacidad:
            raise serializers.ValidationError({'huespedes': 'La capacidad máxima es de {0} huéspedes.'.format(
                publicacion.capacidad)})
        servicios = list(publicacion.servicios.filter(pk__in=set(datos['servicios'])))
        if len(servicios) != len(set(datos['servicios'])):
            raise serializers.ValidationError(
                {'servicios': 'Hay servicios que no pertenecen a este alojamiento.'})
        datos['servicios'] = servicios
        if not publicacion.disponibilidades.filter(fecha_inicio__lte=entrada, fecha_fin__gte=salida).exists():
            raise serializers.ValidationError(
                {'fecha_entrada': 'Las fechas no están dentro de un periodo disponible del alojamiento.'})
        if Reserva.activas_en(publicacion, entrada, salida).exists():
            raise serializers.ValidationError(
                {'fecha_entrada': 'El alojamiento ya está reservado en esas fechas.'})
        return datos


class HistorialSerializador(serializers.ModelSerializer):
    usuario = serializers.SerializerMethodField(method_name='obtener_usuario')

    class Meta:
        model = HistorialReserva
        fields = ['estado_anterior', 'estado_nuevo', 'usuario', 'detalle', 'fecha']

    def obtener_usuario(self, historial):
        return historial.usuario.get_full_name() if historial.usuario else None


class ReservaSerializador(serializers.ModelSerializer):
    publicacion = serializers.SerializerMethodField(method_name='obtener_publicacion')
    huesped = serializers.CharField(source='huesped.get_full_name', read_only=True)
    factura = serializers.CharField(source='factura.numero', read_only=True, default=None)

    class Meta:
        model = Reserva
        fields = ['id', 'codigo', 'publicacion', 'huesped', 'fecha_entrada', 'fecha_salida', 'huespedes',
                  'noches', 'precio_noche', 'precio_base', 'descuento', 'tarifa_limpieza', 'servicios',
                  'total_servicios', 'total', 'estado',
                  'motivo_cancelacion', 'fecha_cancelacion',
                  'fecha_creacion', 'factura']
        read_only_fields = fields

    def obtener_publicacion(self, reserva):
        publicacion = reserva.publicacion
        return {'id': publicacion.pk, 'titulo': publicacion.titulo, 'ciudad': publicacion.ciudad}


class ReservaDetalleSerializador(ReservaSerializador):
    historial = HistorialSerializador(many=True, read_only=True)

    class Meta(ReservaSerializador.Meta):
        fields = ReservaSerializador.Meta.fields + ['historial']
        read_only_fields = fields


class CancelacionSerializador(serializers.Serializer):
    motivo = serializers.CharField(min_length=5, max_length=255, error_messages={
        **obligatorio('Escribe el motivo de la cancelación.'),
        'min_length': 'El motivo debe tener al menos 5 caracteres.'})
