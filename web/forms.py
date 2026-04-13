from django import forms
from .models import Evento, ConfiguracionEvento, GlobalConfig, ProveedorServicio


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'nombre', 'tipo', 'ubicacion',
            'fecha_inicio', 'fecha_fin',
            'descripcion', 'max_asistentes', 'servicios',
        ]
        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin':    forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descripcion':  forms.Textarea(attrs={'rows': 3}),
            'servicios':    forms.CheckboxSelectMultiple(),
        }


class ConfiguracionEventoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEvento
        fields = [
            'tiene_catering', 'tiene_escenario', 'tiene_iluminacion',
            'tiene_seguridad', 'tiene_streaming', 'tiene_decoracion',
            'notas_adicionales',
        ]
        widgets = {
            'notas_adicionales': forms.Textarea(attrs={'rows': 3}),
        }


class GlobalConfigForm(forms.ModelForm):
    class Meta:
        model = GlobalConfig
        fields = [
            'moneda', 'porcentaje_impuestos',
            'limite_asistentes', 'notificaciones_activas',
            'modo_mantenimiento',
        ]


class BuildEventoForm(forms.Form):
    MODE_CHOICES = [
        ('from_scratch', 'Construir desde Cero'),
        ('from_clone',   'Clonar desde Existente'),
    ]
    TIPO_CHOICES = [
        ('conferencia', 'Conferencia'),
        ('boda',        'Boda'),
        ('concierto',   'Concierto'),
        ('teatro',      'Teatro'),
    ]
    CONFIG_CHOICES = [
        ('estandar',    'Estándar'),
        ('completa',    'Completo'),
        ('personalizada', 'Personalizado'),
    ]
    build_mode      = forms.ChoiceField(choices=MODE_CHOICES, initial='from_scratch')
    source_event_id = forms.IntegerField(required=False)
    nombre          = forms.CharField(max_length=200)
    tipo_builder    = forms.ChoiceField(choices=TIPO_CHOICES, required=False)
    configuracion   = forms.ChoiceField(choices=CONFIG_CHOICES, required=False)
    ubicacion       = forms.CharField(max_length=200, required=False)
    fecha_inicio    = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    fecha_fin = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    max_asistentes  = forms.IntegerField(min_value=1, initial=100)
    descripcion     = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), required=False
    )
    tiene_catering   = forms.BooleanField(required=False)
    tiene_escenario  = forms.BooleanField(required=False)
    tiene_iluminacion = forms.BooleanField(required=False)
    tiene_seguridad  = forms.BooleanField(required=False)
    tiene_streaming  = forms.BooleanField(required=False)
    tiene_decoracion = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('build_mode')
        if mode == 'from_scratch':
            if not cleaned.get('tipo_builder'):
                self.add_error('tipo_builder', 'Por favor selecciona un tipo de evento.')
            if not cleaned.get('configuracion'):
                self.add_error('configuracion', 'Por favor selecciona un nivel de configuración.')
        elif mode == 'from_clone':
            if not cleaned.get('source_event_id'):
                self.add_error('source_event_id', 'Por favor selecciona un evento fuente para clonar.')
        return cleaned


class CloneEventoForm(forms.Form):
    nombre       = forms.CharField(max_length=200, label="Nombre del Nuevo Evento")
    fecha_inicio = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Nueva Fecha de Inicio"
    )
    fecha_fin = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Nueva Fecha de Finalización"
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Descripción"
    )
    max_asistentes = forms.IntegerField(min_value=1, label="Máximo de Asistentes")

class SubEventoForm(forms.ModelForm):
    """Form for adding a sub-event under an existing Composite event."""

    class Meta:
        model = Evento
        fields = [
            'nombre', 'tipo', 'ubicacion',
            'fecha_inicio', 'fecha_fin',
            'descripcion', 'max_asistentes', 'presupuesto',
        ]
        widgets = {
            'fecha_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_fin':    forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'descripcion':  forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'presupuesto': 'Presupuesto (USD)',
        }
