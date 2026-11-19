from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from aplicaciones.validacion import (
    normalizar_espacios, validar_solo_digitos, validar_solo_letras, validar_usuario,
)
from .models import Usuario


def obligatorio(texto):
    return {'required': texto, 'blank': texto, 'null': texto}


def validar_nombre(valor, campo):
    valor = normalizar_espacios(valor)
    validar_solo_letras(valor, campo)
    if not 2 <= len(valor) <= 150:
        raise serializers.ValidationError(
            '{0} debe tener entre 2 y 150 caracteres.'.format(campo))
    return valor


def validar_contrasena_del_usuario(contrasena, usuario):
    try:
        validate_password(contrasena, usuario)
    except DjangoValidationError as error:
        raise serializers.ValidationError({'contrasena': error.messages[0]})


def validar_telefono(valor):
    if valor:
        validar_solo_digitos(valor, 'El teléfono')
        if not 7 <= len(valor) <= 15:
            raise serializers.ValidationError('El teléfono debe tener entre 7 y 15 dígitos.')
    return valor


class ContrasenaNuevaSerializador(serializers.Serializer):
    contrasena = serializers.CharField(
        write_only=True, max_length=64, trim_whitespace=False,
        error_messages=obligatorio('Este campo es obligatorio.'))
    confirmar_contrasena = serializers.CharField(
        write_only=True, trim_whitespace=False,
        error_messages=obligatorio('Confirma la contraseña.'))

    def validate_contrasena(self, valor):
        try:
            validate_password(valor)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages[0])
        return valor

    def validate(self, datos):
        if datos['contrasena'] != datos['confirmar_contrasena']:
            raise serializers.ValidationError(
                {'confirmar_contrasena': 'Las dos contraseñas no coinciden.'})
        return datos


class RegistroSerializador(ContrasenaNuevaSerializador):
    nombre_usuario = serializers.CharField(
        max_length=150, error_messages=obligatorio('Escribe el nombre de usuario.'))
    nombres = serializers.CharField(max_length=150, error_messages=obligatorio('Este campo es obligatorio.'))
    apellidos = serializers.CharField(max_length=150, error_messages=obligatorio('Este campo es obligatorio.'))
    correo = serializers.EmailField(max_length=120, error_messages={
        **obligatorio('Este campo es obligatorio.'),
        'invalid': 'Escribe un correo electrónico válido, por ejemplo nombre@dominio.com.',
    })
    telefono = serializers.CharField(error_messages=obligatorio('Este campo es obligatorio.'))
    rol = serializers.CharField(error_messages=obligatorio('Este campo es obligatorio.'))

    def validate_contrasena(self, valor):
        return valor

    def validate_rol(self, valor):
        if valor not in [Usuario.ROL_HUESPED, Usuario.ROL_ANFITRION]:
            raise serializers.ValidationError('Solo puedes registrarte como Huésped o Anfitrión.')
        return valor

    def validate_nombre_usuario(self, valor):
        valor = normalizar_espacios(valor)
        validar_usuario(valor)
        if not 4 <= len(valor) <= 150:
            raise serializers.ValidationError(
                'El nombre de usuario debe tener entre 4 y 150 caracteres.')
        if Usuario.objects.filter(username__iexact=valor).exists():
            raise serializers.ValidationError('Ya existe un usuario con ese nombre de usuario.')
        return valor

    def validate_nombres(self, valor):
        return validar_nombre(valor, 'El campo nombres')

    def validate_apellidos(self, valor):
        return validar_nombre(valor, 'El campo apellidos')

    def validate_correo(self, valor):
        valor = valor.strip().lower()
        if Usuario.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError('El correo ya está registrado')
        return valor

    def validate_telefono(self, valor):
        return validar_telefono(valor)

    def validate(self, datos):
        datos = super().validate(datos)
        validar_contrasena_del_usuario(datos['contrasena'], Usuario(
            username=datos['nombre_usuario'], email=datos['correo'],
            first_name=datos['nombres'], last_name=datos['apellidos']))
        return datos

    def create(self, datos):
        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                username=datos['nombre_usuario'],
                email=datos['correo'],
                password=datos['contrasena'],
                first_name=datos['nombres'],
                last_name=datos['apellidos'],
                telefono=datos.get('telefono', ''),
            )
            usuario.groups.add(Group.objects.get(name=datos['rol']))
        return usuario


class PerfilSerializador(serializers.ModelSerializer):
    nombre_usuario = serializers.CharField(source='username', read_only=True)
    nombres = serializers.CharField(
        source='first_name', max_length=150, error_messages=obligatorio('Este campo es obligatorio.'))
    apellidos = serializers.CharField(
        source='last_name', max_length=150, error_messages=obligatorio('Escribe los apellidos.'))
    correo = serializers.EmailField(source='email', read_only=True)
    rol = serializers.SerializerMethodField(method_name='obtener_rol')

    class Meta:
        model = Usuario
        fields = ['id', 'nombre_usuario', 'nombres', 'apellidos', 'correo', 'telefono', 'rol',
                  'estado', 'motivo_restriccion', 'correo_verificado', 'fecha_registro']
        read_only_fields = ['id', 'estado', 'motivo_restriccion', 'correo_verificado', 'fecha_registro']

    def obtener_rol(self, usuario):
        return usuario.obtener_rol()

    def validate_nombres(self, valor):
        return validar_nombre(valor, 'El campo nombres')

    def validate_apellidos(self, valor):
        return validar_nombre(valor, 'El campo apellidos')

    def validate_telefono(self, valor):
        return validar_telefono(valor)


class CredencialesSerializador(serializers.Serializer):
    correo_o_usuario = serializers.CharField(
        error_messages=obligatorio('Este campo es obligatorio.'))
    contrasena = serializers.CharField(
        trim_whitespace=False, error_messages=obligatorio('Este campo es obligatorio.'))


class CorreoSerializador(serializers.Serializer):
    correo = serializers.EmailField(error_messages=obligatorio('Escribe el correo electrónico.'))


class VerificacionSerializador(serializers.Serializer):
    correo = serializers.EmailField(error_messages=obligatorio('Escribe el correo electrónico.'))
    codigo = serializers.RegexField(r'^[0-9]{6}$', error_messages={
        **obligatorio('Escribe el código de verificación.'),
        'invalid': 'El código tiene 6 dígitos.',
    })


class RestablecerSerializador(ContrasenaNuevaSerializador):
    correo = serializers.EmailField(error_messages=obligatorio('Escribe el correo electrónico.'))
    token = serializers.CharField(error_messages=obligatorio('Falta el código de recuperación.'))


class MotivoSerializador(serializers.Serializer):
    motivo = serializers.CharField(min_length=5, max_length=255, error_messages={
        **obligatorio('Escribe el motivo.'),
        'min_length': 'El motivo debe tener al menos 5 caracteres.',
    })