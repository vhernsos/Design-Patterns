from decimal import Decimal

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

                                                                                
    es_compuesto = models.BooleanField(default=False)
    evento_padre = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='subeventos'
    )
    presupuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

                                                                               
    catering_contratado = models.ForeignKey(
        'ProveedorCatering', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='eventos'
    )
    streaming_contratado = models.ForeignKey(
        'ProveedorStreaming', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='eventos'
    )

                                                                                
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

                                                                                
    decoradores = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de claves de decoradores aplicados al evento",
    )

                                                                                
    tipo_evento = models.CharField(
        max_length=50,
        choices=[
            ('conferencia', 'Conferencia'),
            ('boda', 'Boda'),
            ('concierto', 'Concierto'),
            ('cumpleaños', 'Cumpleaños'),
            ('exposición', 'Exposición'),
            ('otro', 'Otro'),
        ],
        default='otro',
    )
    confirmado = models.BooleanField(default=False)

                                           
    ponentes = models.JSONField(default=list, blank=True, help_text="Lista de ponentes (Conferencia)")
    ceremonia_tipo = models.CharField(max_length=100, blank=True, help_text="Tipo de ceremonia (Boda)")
    artistas = models.JSONField(default=list, blank=True, help_text="Lista de artistas (Concierto)")
    edad_cumple = models.PositiveIntegerField(null=True, blank=True, help_text="Edad del cumpleaños")
    cantidad_obras = models.PositiveIntegerField(null=True, blank=True, help_text="Número de obras (Exposición)")

    def __str__(self):
        return self.nombre

                                                                                

    def es_hoja(self) -> bool:
        return not self.subeventos.exists()

    def obtener_presupuesto_efectivo(self) -> Decimal:
        if self.evento_padre_id:
            return Decimal('0')
        return self.presupuesto or Decimal('0')

    def calcular_presupuesto_total(self) -> float:
        if self.evento_padre_id:
            raise ValueError("Los subeventos no tienen presupuesto independiente")
        return self.obtener_presupuesto_efectivo()

    def calcular_duracion_total(self) -> float:
        delta = self.fecha_fin - self.fecha_inicio
        horas = delta.total_seconds() / 3600
        for sub in self.subeventos.all():
            horas += sub.calcular_duracion_total()
        return round(horas, 2)

    def obtener_capacidad_maxima(self) -> int:
        cap = self.max_asistentes
        for sub in self.subeventos.all():
            sub_cap = sub.obtener_capacidad_maxima()
            if sub_cap > cap:
                cap = sub_cap
        return cap

    def calcular_monto_total(self):
        from web.patterns.calculator import CalculadoraCostes

        return CalculadoraCostes.calcular_costo_total(self)['costo_total']


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
        self.pk = 1                                       
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Global Configuration"


                                                                               

class ProveedorCatering(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} (€{self.precio:,.0f})"


class ProveedorStreaming(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} (€{self.precio:,.0f})"


                                                                                

class ProveedorServicio(models.Model):

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
        if self.tipo.startswith('catering'):
            return 'catering'
        if self.tipo in ('stripe', 'paypal', 'mercadopago'):
            return 'pago'
        return 'streaming'


class ServicioContratado(models.Model):

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

                                                                                 

class Pasarela(models.Model):

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


                                                                                

class HistorialNotificacion(models.Model):

    TIPO_NOTIFICACION = [
        ('evento_creado',       'Evento Creado'),
        ('evento_actualizado',  'Evento Actualizado'),
        ('evento_pagado',       'Evento Pagado'),
        ('evento_cancelado',    'Evento Cancelado'),
        ('evento_fecha_cambió', 'Fecha Cambió'),
        ('evento_estado_cambió','Estado Cambió'),
        ('servicio_contratado', 'Servicio Contratado'),
    ]

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name='notificaciones'
    )
    tipo = models.CharField(max_length=50, choices=TIPO_NOTIFICACION)
    mensaje = models.TextField()
    detalles = models.JSONField(default=dict, blank=True)
    enviado_a = models.CharField(max_length=200)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.evento.nombre} — {self.tipo}"
