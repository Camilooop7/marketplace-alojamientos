import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    ROL_HUESPED = 'Huesped'
    ROL_ANFITRION = 'Anfitrion'
    ROL_ADMINISTRADOR = 'Administrador'

    VIGENCIA_CODIGO_MINUTOS = 15
    ESPERA_REENVIO_SEGUNDOS = 60
    MAXIMO_INTENTOS_CODIGO = 3

    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'
        RESTRINGIDO = 'RESTRINGIDO', 'Restringido'

    email = models.EmailField(max_length=120, unique=True)
    telefono = models.CharField(max_length=15, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ACTIVO)
    motivo_restriccion = models.CharField(max_length=255, blank=True)
    correo_verificado = models.BooleanField(default=False)
    codigo_verificacion = models.CharField(max_length=128, blank=True)
    codigo_enviado = models.DateTimeField(null=True, blank=True)
    codigo_intentos = models.PositiveSmallIntegerField(default=0)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{0} (ID: {1} - Estado: {2})'.format(
            self.get_full_name() or self.username, self.pk, self.estado)

    def obtener_rol(self):
        nombres = sorted(grupo.name for grupo in self.groups.all())
        return ', '.join(nombres) or None

    def es_huesped(self):
        return self.groups.filter(name=self.ROL_HUESPED).exists()

    def es_anfitrion(self):
        return self.groups.filter(name=self.ROL_ANFITRION).exists()

    def es_administrador(self):
        return self.is_superuser or self.groups.filter(name=self.ROL_ADMINISTRADOR).exists()

    def generar_codigo_verificacion(self):
        codigo = '{0:06d}'.format(secrets.randbelow(1000000))
        self.codigo_verificacion = make_password(codigo)
        self.codigo_enviado = timezone.now()
        self.codigo_intentos = 0
        self.save(update_fields=['codigo_verificacion', 'codigo_enviado', 'codigo_intentos'])
        return codigo

    def codigo_vencido(self):
        if not self.codigo_enviado:
            return True
        return timezone.now() > self.codigo_enviado + timedelta(minutes=self.VIGENCIA_CODIGO_MINUTOS)

    def puede_reenviar_codigo(self):
        if not self.codigo_enviado:
            return True
        return timezone.now() >= self.codigo_enviado + timedelta(seconds=self.ESPERA_REENVIO_SEGUNDOS)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.correo_verificado = True
        super().save(*args, **kwargs)
        if self.is_superuser and not self.groups.filter(name=self.ROL_ADMINISTRADOR).exists():
            grupo, _ = Group.objects.get_or_create(name=self.ROL_ADMINISTRADOR)
            self.groups.add(grupo)


class Auditoria(models.Model):

    class Accion(models.TextChoices):
        REGISTRO = 'REGISTRO', 'Registro de usuario'
        VERIFICACION = 'VERIFICACION', 'Verificación de correo'
        INGRESO = 'INGRESO', 'Inicio de sesión'
        SALIDA = 'SALIDA', 'Cierre de sesión'
        ACCESO_FALLIDO = 'ACCESO_FALLIDO', 'Intento fallido de acceso'
        ACTUALIZACION_PERFIL = 'ACTUALIZACION_PERFIL', 'Actualización de perfil'
        CAMBIO_ESTADO = 'CAMBIO_ESTADO', 'Cambio de estado de la cuenta'
        RECUPERACION = 'RECUPERACION', 'Recuperación de contraseña'
        RESTRICCION = 'RESTRICCION', 'Restricción de cuenta'

    class Resultado(models.TextChoices):
        EXITOSO = 'EXITOSO', 'Exitoso'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='auditorias')
    accion = models.CharField(max_length=25, choices=Accion.choices)
    recurso = models.CharField(max_length=100)
    resultado = models.CharField(max_length=10, choices=Resultado.choices, default=Resultado.EXITOSO)
    detalle = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha']

    def __str__(self):
        return '{0} - {1} ({2})'.format(self.usuario, self.get_accion_display(), self.get_resultado_display())

    @classmethod
    def registrar(cls, usuario, accion, recurso, detalle='', resultado=Resultado.EXITOSO):
        return cls.objects.create(
            usuario=usuario, accion=accion, recurso=recurso,
            detalle=detalle[:255], resultado=resultado)