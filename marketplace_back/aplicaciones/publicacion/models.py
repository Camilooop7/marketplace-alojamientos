from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Publicacion(models.Model):

    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        PENDIENTE_REVISION = 'PENDIENTE_REVISION', 'Pendiente de revisión'
        ACTIVA = 'ACTIVA', 'Activa'
        PAUSADA = 'PAUSADA', 'Pausada'
        BLOQUEADA = 'BLOQUEADA', 'Bloqueada'

    class Tipo(models.TextChoices):
        CASA = 'CASA', 'Casa'
        APARTAMENTO = 'APARTAMENTO', 'Apartamento'
        HABITACION = 'HABITACION', 'Habitación'
        CABANA = 'CABANA', 'Cabaña'

    anfitrion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                  related_name='publicaciones')
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(max_length=2000)
    ciudad = models.CharField(max_length=80)
    direccion = models.CharField(max_length=150)
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    capacidad = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    precio_noche = models.DecimalField(max_digits=12, decimal_places=2,
                                       validators=[MinValueValidator(1)])
    tarifa_limpieza = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                          validators=[MinValueValidator(0)])
    descuento_porcentaje = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(90)])
    noches_descuento = models.PositiveSmallIntegerField(default=7, validators=[MinValueValidator(1)])
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return '{0} - {1} ({2})'.format(self.titulo, self.ciudad, self.estado)


class ServicioAdicional(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='servicios')
    nombre = models.CharField(max_length=60)
    precio = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name_plural = 'Servicios adicionales'
        ordering = ['nombre']

    def __str__(self):
        return '{0} (${1})'.format(self.nombre, self.precio)


class Disponibilidad(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE,
                                    related_name='disponibilidades')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        verbose_name_plural = 'Disponibilidades'
        ordering = ['fecha_inicio']
        constraints = [
            models.CheckConstraint(condition=models.Q(fecha_fin__gt=models.F('fecha_inicio')),
                                   name='disponibilidad_fin_posterior_inicio'),
        ]

    def __str__(self):
        return '{0} a {1}'.format(self.fecha_inicio, self.fecha_fin)


class ImagenPublicacion(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='imagenes')
    contenido = models.BinaryField()
    tipo_contenido = models.CharField(max_length=30, default='image/jpeg')
    orden = models.PositiveSmallIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagen de publicación'
        verbose_name_plural = 'Imágenes de publicación'
        ordering = ['orden', 'id']

    def __str__(self):
        return 'Imagen #{0} de la publicación #{1}'.format(self.pk, self.publicacion_id)
