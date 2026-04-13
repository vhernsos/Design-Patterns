from django.contrib import admin
from .models import (
    TipoEvento, Ubicacion, Servicio,
    Evento, ConfiguracionEvento, PlantillaEvento, GlobalConfig,
    ProveedorServicio, ServicioContratado,
)


@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ciudad', 'capacidad']


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio']
    list_filter = ['categoria']


class ConfiguracionEventoInline(admin.StackedInline):
    model = ConfiguracionEvento
    extra = 0


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'fecha_inicio', 'organizador', 'es_clon']
    list_filter = ['tipo', 'es_clon']
    search_fields = ['nombre']
    inlines = [ConfiguracionEventoInline]


@admin.register(GlobalConfig)
class GlobalConfigAdmin(admin.ModelAdmin):
    list_display = [
        'moneda', 'porcentaje_impuestos',
        'limite_asistentes', 'notificaciones_activas', 'modo_mantenimiento',
    ]

    def has_add_permission(self, request):
        return not GlobalConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PlantillaEvento)
class PlantillaEventoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'evento_base', 'creado_en']

@admin.register(ProveedorServicio)
class ProveedorServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activo']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre']


@admin.register(ServicioContratado)
class ServicioContratadoAdmin(admin.ModelAdmin):
    list_display = ['proveedor', 'evento', 'estado', 'fecha_solicitud', 'costo']
    list_filter = ['estado', 'proveedor__tipo']
    search_fields = ['evento__nombre', 'proveedor__nombre']
