from decimal import Decimal

from django.core.management.base import BaseCommand
from web.models import ProveedorCatering, ProveedorStreaming


class Command(BaseCommand):
    help = 'Crea los proveedores de catering y streaming iniciales'

    def handle(self, *args, **options):
        # Catering providers
        catering_data = [
            {
                'nombre': 'Catering Premium',
                'descripcion': 'Menú gourmet con servicio de camareros',
                'precio': Decimal('5000.00'),
            },
            {
                'nombre': 'Catering Estándar',
                'descripcion': 'Menú básico con bebidas incluidas',
                'precio': Decimal('3000.00'),
            },
        ]
        for data in catering_data:
            obj, created = ProveedorCatering.objects.get_or_create(
                nombre=data['nombre'],
                defaults={'descripcion': data['descripcion'], 'precio': data['precio']},
            )
            status = 'creado' if created else 'ya existe'
            self.stdout.write(f'ProveedorCatering "{obj.nombre}" — {status}')

        # Streaming providers
        streaming_data = [
            {
                'nombre': 'Streaming 4K Premium',
                'descripcion': 'Transmisión en 4K con múltiples cámaras',
                'precio': Decimal('8000.00'),
            },
            {
                'nombre': 'Streaming HD Básico',
                'descripcion': 'Transmisión en HD con 1 cámara',
                'precio': Decimal('4000.00'),
            },
        ]
        for data in streaming_data:
            obj, created = ProveedorStreaming.objects.get_or_create(
                nombre=data['nombre'],
                defaults={'descripcion': data['descripcion'], 'precio': data['precio']},
            )
            status = 'creado' if created else 'ya existe'
            self.stdout.write(f'ProveedorStreaming "{obj.nombre}" — {status}')

        self.stdout.write(self.style.SUCCESS('Proveedores creados exitosamente.'))
