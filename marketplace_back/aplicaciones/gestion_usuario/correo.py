from smtplib import SMTPException
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail

from .models import Usuario


def enviar_correo(asunto, mensaje, destino):
    try:
        send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [destino])
        return True
    except (SMTPException, OSError):
        return False


def enviar_codigo_verificacion(usuario, codigo):
    mensaje = (
        'Hola {0},\n\n'
        'Tu código de verificación es: {1}\n\n'
        'El código vence en {2} minutos. Si no creaste esta cuenta, ignora este mensaje.\n'
    ).format(usuario.first_name, codigo, Usuario.VIGENCIA_CODIGO_MINUTOS)
    return enviar_correo('Verifica tu cuenta en el Marketplace', mensaje, usuario.email)


def enviar_enlace_recuperacion(usuario, token):
    enlace = '{0}/restablecer?correo={1}&token={2}'.format(
        settings.FRONTEND_URL.rstrip('/'), quote(usuario.email), token)
    mensaje = (
        'Hola {0},\n\n'
        'Para restablecer tu contraseña entra a este enlace:\n{1}\n\n'
        'El enlace vence en 30 minutos. Si no lo solicitaste, ignora este mensaje.\n'
    ).format(usuario.first_name, enlace)
    return enviar_correo('Restablece tu contraseña del Marketplace', mensaje, usuario.email)