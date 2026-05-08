                                                

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Evento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('fecha_inicio', models.DateTimeField()),
                ('fecha_fin', models.DateTimeField()),
                ('descripcion', models.TextField(blank=True)),
                ('max_asistentes', models.PositiveIntegerField(default=100)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('es_clon', models.BooleanField(default=False)),
                ('evento_original', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clones', to='web.evento')),
                ('organizador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GlobalConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('moneda', models.CharField(default='USD', max_length=10)),
                ('porcentaje_impuestos', models.DecimalField(decimal_places=2, default=16.0, max_digits=5)),
                ('limite_asistentes', models.PositiveIntegerField(default=5000)),
                ('notificaciones_activas', models.BooleanField(default=True)),
                ('modo_mantenimiento', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Global Configuration',
            },
        ),
        migrations.CreateModel(
            name='Servicio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('categoria', models.CharField(choices=[('catering', 'Catering'), ('escenario', 'Stage'), ('iluminacion', 'Lighting'), ('seguridad', 'Security'), ('streaming', 'Streaming'), ('decoracion', 'Decoration'), ('otro', 'Other')], max_length=50)),
                ('descripcion', models.TextField(blank=True)),
                ('precio', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='TipoEvento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ubicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('direccion', models.TextField()),
                ('ciudad', models.CharField(max_length=100)),
                ('capacidad', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='PlantillaEvento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('evento_base', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plantillas', to='web.evento')),
            ],
        ),
        migrations.AddField(
            model_name='evento',
            name='servicios',
            field=models.ManyToManyField(blank=True, to='web.servicio'),
        ),
        migrations.AddField(
            model_name='evento',
            name='tipo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.tipoevento'),
        ),
        migrations.AddField(
            model_name='evento',
            name='ubicacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.ubicacion'),
        ),
        migrations.CreateModel(
            name='ConfiguracionEvento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tiene_catering', models.BooleanField(default=False)),
                ('tiene_escenario', models.BooleanField(default=False)),
                ('tiene_iluminacion', models.BooleanField(default=False)),
                ('tiene_seguridad', models.BooleanField(default=False)),
                ('tiene_streaming', models.BooleanField(default=False)),
                ('tiene_decoracion', models.BooleanField(default=False)),
                ('notas_adicionales', models.TextField(blank=True)),
                ('evento', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='configuracion', to='web.evento')),
            ],
        ),
    ]
