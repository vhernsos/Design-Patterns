from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TipoEvento(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Ubicacion(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} - {self.ciudad}"


class Servicio(models.Model):
    CATEGORIA_CHOICES = [
        ('catering', 'Catering'),
        ('escenario', 'Stage'),
        ('iluminacion', 'Lighting'),
        ('seguridad', 'Security'),
        ('streaming', 'Streaming'),
        ('decoracion', 'Decoration'),
        ('otro', 'Other'),
    ]
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"


class Evento(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.ForeignKey(TipoEvento, on_delete=models.SET_NULL, null=True)
    ubicacion = models.ForeignKey(
        Ubicacion, on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    descripcion = models.TextField(blank=True)
    max_asistentes = models.PositiveIntegerField(default=100)
    organizador = models.ForeignKey(User, on_delete=models.CASCADE)
    servicios = models.ManyToManyField(Servicio, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    es_clon = models.BooleanField(default=False)
    evento_original = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='clones'
    )

    # ── Composite pattern fields ──────────────────────────────────────────────
    es_compuesto = models.BooleanField(default=False)
    evento_padre = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='subeventos'
    )
    presupuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── External services (Adapter pattern) ──────────────────────────────────
    catering_contratado = models.ForeignKey(
        'ProveedorCatering', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='eventos'
    )
    streaming_contratado = models.ForeignKey(
        'ProveedorStreaming', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='eventos'
    )

    # ── Payment fields ────────────────────────────────────────────────────────
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.nombre

    # ── Composite helpers ─────────────────────────────────────────────────────

    def es_hoja(self) -> bool:
        """True if this event has no sub-events (leaf node in Composite tree)."""
        return not self.subeventos.exists()

    def calcular_presupuesto_total(self) -> float:
        """Recursively sum budgets of self and all descendants."""
        total = float(self.presupuesto)
        for sub in self.subeventos.all():
            total += sub.calcular_presupuesto_total()
        return total

    def calcular_duracion_total(self) -> float:
        """Recursively sum duration (hours) of self and all descendants."""
        delta = self.fecha_fin - self.fecha_inicio
        horas = delta.total_seconds() / 3600
        for sub in self.subeventos.all():
            horas += sub.calcular_duracion_total()
        return round(horas, 2)

    def obtener_capacidad_maxima(self) -> int:
        """Return maximum capacity across self and all descendants."""
        cap = self.max_asistentes
        for sub in self.subeventos.all():
            sub_cap = sub.obtener_capacidad_maxima()
            if sub_cap > cap:
                cap = sub_cap
        return cap

    def calcular_monto_total(self):
        """Calculates total amount: base budget + sub-events budgets."""
        from decimal import Decimal
        total = self.presupuesto or Decimal('0')
        for sub in self.subeventos.all():
            total += sub.presupuesto or Decimal('0')
        return total


class ConfiguracionEvento(models.Model):
    evento = models.OneToOneField(
        Evento, on_delete=models.CASCADE, related_name='configuracion'
    )
    tiene_catering = models.BooleanField(default=False)
    tiene_escenario = models.BooleanField(default=False)
    tiene_iluminacion = models.BooleanField(default=False)
    tiene_seguridad = models.BooleanField(default=False)
    tiene_streaming = models.BooleanField(default=False)
    tiene_decoracion = models.BooleanField(default=False)
    notas_adicionales = models.TextField(blank=True)

    def __str__(self):
        return f"Config - {self.evento.nombre}"


class PlantillaEvento(models.Model):
    nombre = models.CharField(max_length=200)
    evento_base = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name='plantillas'
    )
    descripcion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class GlobalConfig(models.Model):
    """Database-backed storage for the Singleton pattern."""
    moneda = models.CharField(max_length=10, default='USD')
    porcentaje_impuestos = models.DecimalField(
        max_digits=5, decimal_places=2, default=16.00
    )
    limite_asistentes = models.PositiveIntegerField(default=5000)
    notificaciones_activas = models.BooleanField(default=True)
    modo_mantenimiento = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Global Configuration'

    def save(self, *args, **kwargs):
        self.pk = 1                   # enforce single row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Global Configuration"


# ── Adapter pattern: Catering and Streaming providers ────────────────────────

class ProveedorCatering(models.Model):
    """Available catering providers that can be contracted for an event."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} (€{self.precio:,.0f})"


class ProveedorStreaming(models.Model):
    """Available streaming providers that can be contracted for an event."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} (€{self.precio:,.0f})"


# ── Adapter pattern: external service providers ───────────────────────────────

class ProveedorServicio(models.Model):
    """Stores credentials and metadata for external service providers."""

    TIPO_CHOICES = [
        ('catering_a',   'Catering – Proveedor A'),
        ('catering_b',   'Catering – Proveedor B'),
        ('stripe',       'Pago – Stripe'),
        ('paypal',       'Pago – PayPal'),
        ('mercadopago',  'Pago – MercadoPago'),
        ('youtube',      'Streaming – YouTube'),
        ('vimeo',        'Streaming – Vimeo'),
        ('facebook',     'Streaming – Facebook Live'),
    ]

    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    api_key = models.CharField(max_length=300, blank=True, help_text='API key / credentials (simulated)')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    @property
    def categoria(self):
        """Returns 'catering', 'pago', or 'streaming' based on tipo."""
        if self.tipo.startswith('catering'):
            return 'catering'
        if self.tipo in ('stripe', 'paypal', 'mercadopago'):
            return 'pago'
        return 'streaming'


class ServicioContratado(models.Model):
    """Records when an event contracts an external service via an Adapter."""

    ESTADO_CHOICES = [
        ('pendiente',   'Pendiente'),
        ('confirmado',  'Confirmado'),
        ('completado',  'Completado'),
        ('cancelado',   'Cancelado'),
    ]

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name='servicios_contratados'
    )
    proveedor = models.ForeignKey(
        ProveedorServicio, on_delete=models.CASCADE, related_name='contratos'
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True)
    respuesta_adapter = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.proveedor.nombre} → {self.evento.nombre} [{self.estado}]"

# ── Payment gateway models ─────────────────────────────────────────────────────

class Pasarela(models.Model):
    """Represents a payment gateway (Stripe, PayPal, MercadoPago)."""

    TIPO_CHOICES = [
        ('stripe',       'Stripe'),
        ('paypal',       'PayPal'),
        ('mercadopago',  'MercadoPago'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=10, default='💳')
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Transaccion(models.Model):
    """Records a payment transaction for an event."""

    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('procesada',  'Procesada'),
        ('fallida',    'Fallida'),
    ]

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name='transacciones'
    )
    pasarela = models.ForeignKey(
        Pasarela, on_delete=models.SET_NULL, null=True, related_name='transacciones'
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    referencia_externa = models.CharField(max_length=200, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transacciones')

    def __str__(self):
        return f"{self.pasarela} — {self.evento.nombre} [{self.estado}]"
