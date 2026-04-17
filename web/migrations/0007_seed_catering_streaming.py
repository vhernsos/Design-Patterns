from django.db import migrations


def seed_proveedores(apps, schema_editor):
    ProveedorCatering = apps.get_model('web', 'ProveedorCatering')
    ProveedorStreaming = apps.get_model('web', 'ProveedorStreaming')

    ProveedorCatering.objects.get_or_create(
        nombre='Catering Premium',
        defaults={
            'descripcion': 'Servicio de catering de alta gama con menú gourmet personalizado.',
            'precio': 5000,
        },
    )
    ProveedorCatering.objects.get_or_create(
        nombre='Catering Estándar',
        defaults={
            'descripcion': 'Servicio de catering estándar con menú variado y económico.',
            'precio': 3000,
        },
    )

    ProveedorStreaming.objects.get_or_create(
        nombre='Streaming 4K Premium',
        defaults={
            'descripcion': 'Transmisión en vivo en calidad 4K Ultra HD con hasta 100.000 espectadores.',
            'precio': 8000,
        },
    )
    ProveedorStreaming.objects.get_or_create(
        nombre='Streaming HD Básico',
        defaults={
            'descripcion': 'Transmisión en vivo en calidad Full HD con hasta 10.000 espectadores.',
            'precio': 4000,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_add_catering_streaming_providers'),
    ]

    operations = [
        migrations.RunPython(seed_proveedores, migrations.RunPython.noop),
    ]
