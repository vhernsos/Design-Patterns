from rest_framework import serializers
from .models import TipoEvento, Ubicacion, Evento, ConfiguracionEvento


class TipoEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEvento
        fields = ['id', 'nombre']
        read_only_fields = ['id']


class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = ['id', 'nombre', 'direccion', 'ciudad']
        read_only_fields = ['id']


class ConfiguracionEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionEvento
        fields = [
            'evento', 'tiene_catering', 'tiene_escenario', 'tiene_iluminacion',
            'tiene_seguridad', 'tiene_streaming', 'tiene_decoracion',
        ]
        read_only_fields = ['evento']


class EventoSerializer(serializers.ModelSerializer):
    tipo = TipoEventoSerializer(read_only=True)
    tipo_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoEvento.objects.all(), source='tipo', write_only=True, required=False, allow_null=True
    )
    ubicacion = UbicacionSerializer(read_only=True)
    ubicacion_id = serializers.PrimaryKeyRelatedField(
        queryset=Ubicacion.objects.all(), source='ubicacion', write_only=True, required=False, allow_null=True
    )
    organizador = serializers.StringRelatedField(read_only=True)
    configuracion = ConfiguracionEventoSerializer(read_only=True)

    class Meta:
        model = Evento
        fields = [
            'id', 'nombre', 'tipo', 'tipo_id', 'ubicacion', 'ubicacion_id',
            'fecha_inicio', 'fecha_fin', 'descripcion', 'max_asistentes',
            'organizador', 'configuracion', 'creado_en',
        ]
        read_only_fields = ['id', 'organizador', 'creado_en']


class ListEventoSerializer(serializers.ModelSerializer):
    tipo = TipoEventoSerializer(read_only=True)
    organizador = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Evento
        fields = ['id', 'nombre', 'tipo', 'fecha_inicio', 'fecha_fin', 'organizador']
