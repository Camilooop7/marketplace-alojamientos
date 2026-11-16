import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('publicacion', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Reserva',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(editable=False, max_length=12, unique=True)),
                ('fecha_entrada', models.DateField()),
                ('fecha_salida', models.DateField()),
                ('huespedes', models.PositiveSmallIntegerField()),
                ('noches', models.PositiveSmallIntegerField()),
                ('precio_noche', models.DecimalField(decimal_places=2, max_digits=12)),
                ('precio_base', models.DecimalField(decimal_places=2, max_digits=12)),
                ('descuento', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('tarifa_limpieza', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_servicios', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('servicios', models.JSONField(blank=True, default=list)),
                ('porcentaje_tarifa_servicio', models.DecimalField(decimal_places=2, max_digits=5)),
                ('tarifa_servicio', models.DecimalField(decimal_places=2, max_digits=12)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('estado', models.CharField(choices=[('PENDIENTE_PAGO', 'Pendiente de pago'), ('CONFIRMADA', 'Confirmada'), ('CANCELADA', 'Cancelada'), ('COMPLETADA', 'Completada')], default='PENDIENTE_PAGO', max_length=15)),
                ('clave_idempotencia', models.CharField(blank=True, max_length=64)),
                ('motivo_cancelacion', models.CharField(blank=True, max_length=255)),
                ('fecha_cancelacion', models.DateTimeField(blank=True, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('huesped', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservas', to=settings.AUTH_USER_MODEL)),
                ('publicacion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservas', to='publicacion.publicacion')),
            ],
            options={
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='HistorialReserva',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_anterior', models.CharField(blank=True, max_length=15)),
                ('estado_nuevo', models.CharField(max_length=15)),
                ('detalle', models.CharField(blank=True, max_length=255)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('reserva', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial', to='reserva.reserva')),
            ],
            options={
                'verbose_name_plural': 'Historial de reservas',
                'ordering': ['fecha', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(blank=True, max_length=20, unique=True)),
                ('cliente_nombre', models.CharField(max_length=301)),
                ('cliente_correo', models.EmailField(max_length=120)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('estado', models.CharField(choices=[('EMITIDA', 'Emitida - pendiente de pago'), ('ANULADA', 'Anulada')], default='EMITIDA', max_length=10)),
                ('fecha_generacion', models.DateTimeField(auto_now_add=True)),
                ('reserva', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='factura', to='reserva.reserva')),
            ],
            options={
                'ordering': ['-fecha_generacion'],
            },
        ),
        migrations.AddConstraint(
            model_name='reserva',
            constraint=models.CheckConstraint(condition=models.Q(('fecha_salida__gt', models.F('fecha_entrada'))), name='reserva_salida_posterior_entrada'),
        ),
        migrations.AddConstraint(
            model_name='reserva',
            constraint=models.UniqueConstraint(condition=models.Q(('clave_idempotencia', ''), _negated=True), fields=('huesped', 'clave_idempotencia'), name='reserva_clave_idempotencia_unica'),
        ),
    ]
