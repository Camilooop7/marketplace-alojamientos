import re

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .correo import enviar_codigo_verificacion, enviar_enlace_reactivacion, enviar_enlace_recuperacion
from .models import Auditoria, Usuario
from .seguridad import SoloAdministrador, token_reactivacion
from .serializador import (
    CambioContrasenaSerializador, CorreoSerializador, CredencialesSerializador, MotivoSerializador,
    PerfilSerializador, ReactivacionSerializador, RegistroSerializador, RestablecerSerializador,
    VerificacionSerializador, validar_contrasena_del_usuario,
)


@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({'mensaje': 'Cookie CSRF lista.'})


class VistaPublica(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


TOKEN_RECUPERACION = re.compile(r'[0-9a-z]+-[0-9a-f]{32}')


def obtener_usuario(pk):
    usuario = Usuario.objects.filter(pk=pk).first()
    if usuario is None:
        raise NotFound('No encontrado.')
    return usuario


def recurso_usuario(usuario):
    return 'Usuario #{0}'.format(usuario.pk)


def buscar_por_correo(correo):
    return Usuario.objects.filter(email__iexact=correo).first()


def autenticar_credenciales(request, datos):
    usuario = authenticate(
        request, username=datos['correo_o_usuario'], password=datos['contrasena'])
    if usuario is None:
        Auditoria.registrar(
            None, Auditoria.Accion.ACCESO_FALLIDO,
            'Cuenta {0}'.format(datos['correo_o_usuario']),
            'Credenciales incorrectas', Auditoria.Resultado.RECHAZADO)
    return usuario


def rechazar_ingreso(usuario):
    if usuario.estado == Usuario.Estado.RESTRINGIDO:
        detalle = 'Intento de ingreso con la cuenta restringida'
        datos = {'mensaje': 'Tu cuenta está restringida. Motivo: {0}'.format(
            usuario.motivo_restriccion or 'no especificado'), 'estado': usuario.estado}
    elif usuario.estado == Usuario.Estado.INACTIVO:
        detalle = 'Intento de ingreso con la cuenta desactivada'
        datos = {'mensaje': 'Tu cuenta está desactivada. Puedes reactivarla.',
                 'estado': usuario.estado, 'requiere_reactivacion': True, 'correo': usuario.email}
    elif not usuario.correo_verificado:
        detalle = 'Intento de ingreso con el correo sin verificar'
        datos = {'mensaje': 'Debes verificar tu correo antes de ingresar. '
                            'Revisa el código que te enviamos.',
                 'requiere_verificacion': True, 'correo': usuario.email}
    else:
        return None
    Auditoria.registrar(
        usuario, Auditoria.Accion.ACCESO_FALLIDO, recurso_usuario(usuario),
        detalle, Auditoria.Resultado.RECHAZADO)
    return Response(datos, status=status.HTTP_403_FORBIDDEN)


class RegistroView(VistaPublica):
    def post(self, request):
        serializador = RegistroSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        usuario = serializador.save()
        Auditoria.registrar(
            usuario, Auditoria.Accion.REGISTRO, recurso_usuario(usuario),
            'Se registró como {0}'.format(usuario.obtener_rol()))
        enviado = enviar_codigo_verificacion(usuario, usuario.generar_codigo_verificacion())
        if enviado:
            mensaje = 'Cuenta creada. Te enviamos un código de verificación a tu correo.'
        else:
            mensaje = 'Cuenta creada, pero no pudimos enviar el correo. Solicita un código nuevo.'
        return Response(
            {'mensaje': mensaje, 'correo': usuario.email,
             'requiere_verificacion': True, 'correo_enviado': enviado},
            status=status.HTTP_201_CREATED)


class VerificarCorreoView(VistaPublica):
    def post(self, request):
        serializador = VerificacionSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        datos = serializador.validated_data
        invalido = Response({'mensaje': 'El código no es válido o ya venció.'},
                            status=status.HTTP_400_BAD_REQUEST)
        usuario = buscar_por_correo(datos['correo'])
        if usuario is None:
            return invalido
        if usuario.correo_verificado:
            return Response({'mensaje': 'Tu correo ya está verificado. Inicia sesión.'},
                            status=status.HTTP_409_CONFLICT)
        if usuario.codigo_intentos >= Usuario.MAXIMO_INTENTOS_CODIGO:
            return Response({'mensaje': 'Superaste los intentos permitidos. Solicita un código nuevo.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        if usuario.codigo_vencido() or not check_password(datos['codigo'], usuario.codigo_verificacion):
            usuario.codigo_intentos += 1
            usuario.save(update_fields=['codigo_intentos'])
            return invalido
        usuario.correo_verificado = True
        usuario.codigo_verificacion = ''
        usuario.save(update_fields=['correo_verificado', 'codigo_verificacion'])
        Auditoria.registrar(
            usuario, Auditoria.Accion.VERIFICACION, recurso_usuario(usuario), 'Verificó su correo')
        return Response({'mensaje': 'Correo verificado. Ya puedes iniciar sesión.'})


class ReenviarCodigoView(VistaPublica):
    def post(self, request):
        serializador = CorreoSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        usuario = buscar_por_correo(serializador.validated_data['correo'])
        if usuario is not None and not usuario.correo_verificado:
            if not usuario.puede_reenviar_codigo():
                return Response({'mensaje': 'Espera un minuto antes de pedir otro código.'},
                                status=status.HTTP_429_TOO_MANY_REQUESTS)
            if not enviar_codigo_verificacion(usuario, usuario.generar_codigo_verificacion()):
                return Response({'mensaje': 'No se pudo enviar el correo. Inténtalo más tarde.'},
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'mensaje': 'Si la cuenta existe y no está verificada, te enviamos un código nuevo.'})


class IngresarView(VistaPublica):
    def post(self, request):
        serializador = CredencialesSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        usuario = autenticar_credenciales(request, serializador.validated_data)
        if usuario is None:
            return Response({'mensaje': 'Correo o contraseña incorrectos'},
                            status=status.HTTP_401_UNAUTHORIZED)
        rechazo = rechazar_ingreso(usuario)
        if rechazo is not None:
            return rechazo
        login(request, usuario)
        Auditoria.registrar(usuario, Auditoria.Accion.INGRESO, recurso_usuario(usuario), 'Inició sesión')
        return Response({'mensaje': 'Sesión iniciada.', 'usuario': PerfilSerializador(usuario).data})


class SalirView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Auditoria.registrar(
            request.user, Auditoria.Accion.SALIDA, recurso_usuario(request.user), 'Cerró sesión')
        logout(request)
        return Response({'mensaje': 'Sesión cerrada.'})


class RecuperarView(VistaPublica):
    def post(self, request):
        serializador = CorreoSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        usuario = buscar_por_correo(serializador.validated_data['correo'])
        if usuario is not None:
            token = default_token_generator.make_token(usuario)
            Auditoria.registrar(
                usuario, Auditoria.Accion.RECUPERACION, recurso_usuario(usuario),
                'Solicitó recuperar la contraseña')
            if not enviar_enlace_recuperacion(usuario, token):
                return Response({'mensaje': 'No se pudo enviar el correo. Inténtalo más tarde.'},
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'mensaje': 'Si el correo está registrado, se generó un enlace para restablecer '
                                    'tu contraseña.'})


class RestablecerView(VistaPublica):
    def post(self, request):
        serializador = RestablecerSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        datos = serializador.validated_data
        usuario = buscar_por_correo(datos['correo'])
        if usuario is None or not default_token_generator.check_token(usuario, datos['token']):
            mensaje = ('El enlace expiró, solicita uno nuevo' if TOKEN_RECUPERACION.fullmatch(datos['token'])
                       else 'El enlace de recuperación no es válido o ya venció.')
            return Response({'mensaje': mensaje}, status=status.HTTP_400_BAD_REQUEST)
        validar_contrasena_del_usuario(datos['contrasena'], usuario)
        usuario.set_password(datos['contrasena'])
        usuario.save(update_fields=['password'])
        Auditoria.registrar(
            usuario, Auditoria.Accion.RECUPERACION, recurso_usuario(usuario),
            'Restableció la contraseña')
        return Response({'mensaje': 'Contraseña actualizada. Ya puedes iniciar sesión.'})


class SolicitarReactivacionView(VistaPublica):
    def post(self, request):
        serializador = CorreoSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        usuario = buscar_por_correo(serializador.validated_data['correo'])
        if usuario is not None and usuario.estado == Usuario.Estado.INACTIVO:
            Auditoria.registrar(
                usuario, Auditoria.Accion.CAMBIO_ESTADO, recurso_usuario(usuario),
                'Solicitó reactivar su cuenta')
            if not enviar_enlace_reactivacion(usuario, token_reactivacion.make_token(usuario)):
                return Response({'mensaje': 'No se pudo enviar el correo. Inténtalo más tarde.'},
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'mensaje': 'Si la cuenta existe y está desactivada, te enviamos un enlace '
                                    'para reactivarla.'})


class ReactivarView(VistaPublica):
    def post(self, request):
        serializador = ReactivacionSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        datos = serializador.validated_data
        usuario = buscar_por_correo(datos['correo'])
        if usuario is not None and usuario.estado == Usuario.Estado.RESTRINGIDO:
            return Response(
                {'mensaje': 'Tu cuenta fue restringida por un administrador y no puede reactivarse.'},
                status=status.HTTP_403_FORBIDDEN)
        if usuario is None or not token_reactivacion.check_token(usuario, datos['token']):
            return Response({'mensaje': 'El enlace de reactivación no es válido o ya venció.'},
                            status=status.HTTP_400_BAD_REQUEST)
        usuario.estado = Usuario.Estado.ACTIVO
        usuario.save(update_fields=['estado'])
        Auditoria.registrar(
            usuario, Auditoria.Accion.CAMBIO_ESTADO, recurso_usuario(usuario), 'Reactivó su cuenta')
        return Response({'mensaje': 'Tu cuenta fue reactivada. Ya puedes iniciar sesión.'})


class PerfilView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get(self, request):
        return Response(PerfilSerializador(request.user).data)

    def put(self, request):
        serializador = PerfilSerializador(request.user, data=request.data, partial=True)
        serializador.is_valid(raise_exception=True)
        serializador.save()
        Auditoria.registrar(
            request.user, Auditoria.Accion.ACTUALIZACION_PERFIL, recurso_usuario(request.user),
            'Actualizó su perfil')
        return Response({'mensaje': 'Tus datos se actualizaron correctamente.',
                         'usuario': serializador.data})


class CambiarContrasenaView(APIView):
    def post(self, request):
        serializador = CambioContrasenaSerializador(data=request.data, context={'usuario': request.user})
        serializador.is_valid(raise_exception=True)
        request.user.set_password(serializador.validated_data['contrasena'])
        request.user.save(update_fields=['password'])
        update_session_auth_hash(request, request.user)
        Auditoria.registrar(
            request.user, Auditoria.Accion.ACTUALIZACION_PERFIL, recurso_usuario(request.user),
            'Cambió su contraseña')
        return Response({'mensaje': 'Tu contraseña se cambió correctamente.'})


class DesactivarCuentaView(APIView):
    def patch(self, request):
        from aplicaciones.publicacion.models import Publicacion
        from aplicaciones.reserva.models import Reserva

        usuario = request.user
        pendientes = list(Reserva.futuras_de(usuario).values_list('codigo', flat=True))
        if pendientes:
            return Response({'mensaje': 'No puedes desactivar tu cuenta porque tienes reservas pendientes: '
                                        '{0}.'.format(', '.join(pendientes)), 'reservas': pendientes},
                            status=status.HTTP_409_CONFLICT)
        usuario.estado = Usuario.Estado.INACTIVO
        usuario.save(update_fields=['estado'])
        usuario.publicaciones.filter(estado=Publicacion.Estado.ACTIVA).update(
            estado=Publicacion.Estado.PAUSADA)
        Auditoria.registrar(
            usuario, Auditoria.Accion.CAMBIO_ESTADO, recurso_usuario(usuario), 'Desactivó su cuenta')
        logout(request)
        return Response({'mensaje': 'Tu cuenta fue desactivada. Puedes reactivarla cuando quieras.',
                         'estado': Usuario.Estado.INACTIVO})


class UsuarioListaAdminView(ListAPIView):
    permission_classes = [SoloAdministrador]
    serializer_class = PerfilSerializador
    queryset = Usuario.objects.prefetch_related('groups').order_by('last_name', 'first_name')


class RestringirUsuarioView(APIView):
    permission_classes = [SoloAdministrador]

    def post(self, request, pk):
        usuario = obtener_usuario(pk)
        if usuario.pk == request.user.pk:
            return Response({'mensaje': 'No puedes restringir tu propia cuenta.'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializador = MotivoSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        usuario.estado = Usuario.Estado.RESTRINGIDO
        usuario.motivo_restriccion = serializador.validated_data['motivo']
        usuario.save(update_fields=['estado', 'motivo_restriccion'])
        Auditoria.registrar(
            request.user, Auditoria.Accion.RESTRICCION, recurso_usuario(usuario),
            'Restringió la cuenta. Motivo: {0}'.format(usuario.motivo_restriccion))
        return Response({'mensaje': 'La cuenta fue restringida.',
                         'usuario': PerfilSerializador(usuario).data})


class LiberarUsuarioView(APIView):
    permission_classes = [SoloAdministrador]

    def post(self, request, pk):
        usuario = obtener_usuario(pk)
        if usuario.estado != Usuario.Estado.RESTRINGIDO:
            return Response({'mensaje': 'La cuenta no está restringida.'},
                            status=status.HTTP_409_CONFLICT)
        usuario.estado = Usuario.Estado.ACTIVO
        usuario.motivo_restriccion = ''
        usuario.save(update_fields=['estado', 'motivo_restriccion'])
        Auditoria.registrar(
            request.user, Auditoria.Accion.RESTRICCION, recurso_usuario(usuario),
            'Levantó la restricción de la cuenta')
        return Response({'mensaje': 'La restricción fue levantada.',
                         'usuario': PerfilSerializador(usuario).data})