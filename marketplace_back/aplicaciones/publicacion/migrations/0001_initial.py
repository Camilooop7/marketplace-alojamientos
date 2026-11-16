import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Publicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120)),
                ('descripcion', models.TextField(max_length=2000)),
                ('ciudad', models.CharField(max_length=80)),
                ('direccion', models.CharField(max_length=150)),
                ('tipo', models.CharField(choices=[('CASA', 'Casa'), ('APARTAMENTO', 'Apartamento'), ('HABITACION', 'Habitación'), ('CABANA', 'Cabaña')], max_length=12)),
                ('capacidad', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('precio_noche', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(1)])),
                ('tarifa_limpieza', models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('descuento_porcentaje', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(90)])),
                ('noches_descuento', models.PositiveSmallIntegerField(default=7, validators=[django.core.validators.MinValueValidator(1)])),
                ('estado', models.CharField(choices=[('BORRADOR', 'Borrador'), ('PENDIENTE_REVISION', 'Pendiente de revisión'), ('ACTIVA', 'Activa'), ('PAUSADA', 'Pausada'), ('BLOQUEADA', 'Bloqueada')], default='BORRADOR', max_length=20)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('anfitrion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='publicaciones', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Publicación',
                'verbose_name_plural': 'Publicaciones',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='ImagenPublicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido', models.BinaryField()),
                ('tipo_contenido', models.CharField(default='image/jpeg', max_length=30)),
                ('orden', models.PositiveSmallIntegerField(default=0)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('publicacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes', to='publicacion.publicacion')),
            ],
            options={
                'verbose_name': 'Imagen de publicación',
                'verbose_name_plural': 'Imágenes de publicación',
                'ordering': ['orden', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ServicioAdicional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=60)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('publicacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='servicios', to='publicacion.publicacion')),
            ],
            options={
                'verbose_name_plural': 'Servicios adicionales',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Disponibilidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('publicacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disponibilidades', to='publicacion.publicacion')),
            ],
            options={
                'verbose_name_plural': 'Disponibilidades',
                'ordering': ['fecha_inicio'],
                'constraints': [models.CheckConstraint(condition=models.Q(('fecha_fin__gt', models.F('fecha_inicio'))), name='disponibilidad_fin_posterior_inicio')],
            },
        ),
    ]
