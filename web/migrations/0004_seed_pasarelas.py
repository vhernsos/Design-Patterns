from django.db import migrations


def seed_pasarelas(apps, schema_editor):
    Pasarela = apps.get_model('web', 'Pasarela')
    pasarelas = [
        {'nombre': 'Stripe', 'tipo': 'stripe', 'descripcion': 'Pasarela de pago Stripe', 'icono': '💳', 'activa': True},
        {'nombre': 'PayPal', 'tipo': 'paypal', 'descripcion': 'Pasarela de pago PayPal', 'icono': '🅿️', 'activa': True},
        {'nombre': 'MercadoPago', 'tipo': 'mercadopago', 'descripcion': 'Pasarela de pago MercadoPago', 'icono': '💰', 'activa': True},
    ]
    for p in pasarelas:
        Pasarela.objects.get_or_create(tipo=p['tipo'], defaults=p)


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_add_payment_models'),
    ]

    operations = [
        migrations.RunPython(seed_pasarelas, migrations.RunPython.noop),
    ]
