                                                

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0007_seed_catering_streaming'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='artistas',
            field=models.JSONField(blank=True, default=list, help_text='Lista de artistas (Concierto)'),
        ),
        migrations.AddField(
            model_name='evento',
            name='cantidad_obras',
            field=models.PositiveIntegerField(blank=True, help_text='Número de obras (Exposición)', null=True),
        ),
        migrations.AddField(
            model_name='evento',
            name='ceremonia_tipo',
            field=models.CharField(blank=True, help_text='Tipo de ceremonia (Boda)', max_length=100),
        ),
        migrations.AddField(
            model_name='evento',
            name='confirmado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='evento',
            name='decoradores',
            field=models.JSONField(blank=True, default=list, help_text='Lista de claves de decoradores aplicados al evento'),
        ),
        migrations.AddField(
            model_name='evento',
            name='edad_cumple',
            field=models.PositiveIntegerField(blank=True, help_text='Edad del cumpleaños', null=True),
        ),
        migrations.AddField(
            model_name='evento',
            name='ponentes',
            field=models.JSONField(blank=True, default=list, help_text='Lista de ponentes (Conferencia)'),
        ),
        migrations.AddField(
            model_name='evento',
            name='tipo_evento',
            field=models.CharField(choices=[('conferencia', 'Conferencia'), ('boda', 'Boda'), ('concierto', 'Concierto'), ('cumpleaños', 'Cumpleaños'), ('exposición', 'Exposición'), ('otro', 'Otro')], default='otro', max_length=50),
        ),
        migrations.CreateModel(
            name='HistorialNotificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('evento_creado', 'Evento Creado'), ('evento_actualizado', 'Evento Actualizado'), ('evento_pagado', 'Evento Pagado'), ('evento_cancelado', 'Evento Cancelado'), ('evento_fecha_cambió', 'Fecha Cambió'), ('evento_estado_cambió', 'Estado Cambió'), ('servicio_contratado', 'Servicio Contratado')], max_length=50)),
                ('mensaje', models.TextField()),
                ('detalles', models.JSONField(blank=True, default=dict)),
                ('enviado_a', models.CharField(max_length=200)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones', to='web.evento')),
            ],
            options={
                'ordering': ['-fecha'],
            },
        ),
    ]
