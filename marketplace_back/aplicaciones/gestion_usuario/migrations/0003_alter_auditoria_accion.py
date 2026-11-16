from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_usuario', '0002_roles_base'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditoria',
            name='accion',
            field=models.CharField(choices=[('REGISTRO', 'Registro de usuario'), ('VERIFICACION', 'Verificación de correo'), ('INGRESO', 'Inicio de sesión'), ('SALIDA', 'Cierre de sesión'), ('ACCESO_FALLIDO', 'Intento fallido de acceso'), ('ACTUALIZACION_PERFIL', 'Actualización de perfil'), ('CAMBIO_ESTADO', 'Cambio de estado de la cuenta'), ('RECUPERACION', 'Recuperación de contraseña'), ('RESTRICCION', 'Restricción de cuenta'), ('PUBLICACION', 'Gestión de publicación'), ('RESERVA', 'Creación de reserva'), ('CANCELACION', 'Cancelación de reserva'), ('FACTURA', 'Generación de factura')], max_length=25),
        ),
    ]
