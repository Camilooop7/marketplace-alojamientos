from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission

from .models import Usuario


class SesionAutenticacion(SessionAuthentication):
    def authenticate_header(self, request):
        return 'Session'


class CuentaHabilitada(BasePermission):
    message = 'Tu cuenta no está habilitada para realizar esta acción.'

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated
                    and usuario.estado == Usuario.Estado.ACTIVO)


class SoloAdministrador(CuentaHabilitada):
    message = 'Solo el administrador puede realizar esta acción.'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.es_administrador()


class SoloAnfitrion(CuentaHabilitada):
    message = 'Solo un anfitrión puede realizar esta acción.'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.es_anfitrion()


def manejador_excepciones(exc, contexto):
    from rest_framework.views import exception_handler
    respuesta = exception_handler(exc, contexto)
    if respuesta is not None and isinstance(respuesta.data, dict) and 'detail' in respuesta.data:
        respuesta.data = {'mensaje': str(respuesta.data['detail'])}
    return respuesta