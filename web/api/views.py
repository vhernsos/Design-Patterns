from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from ..models import TipoEvento, Ubicacion, Evento, ConfiguracionEvento
from ..serializers import (
    TipoEventoSerializer, UbicacionSerializer,
    EventoSerializer, ListEventoSerializer,
    ConfiguracionEventoSerializer,
)


class TipoEventoViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista y detalle de tipos de evento (solo lectura)."""
    queryset = TipoEvento.objects.all()
    serializer_class = TipoEventoSerializer
    permission_classes = [permissions.IsAuthenticated]


class UbicacionViewSet(viewsets.ModelViewSet):
    """CRUD completo de ubicaciones."""
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer
    permission_classes = [permissions.IsAuthenticated]


class EventoViewSet(viewsets.ModelViewSet):
    """CRUD completo de eventos del usuario autenticado."""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo']
    search_fields = ['nombre']
    ordering_fields = ['creado_en', 'fecha_inicio', 'nombre']
    ordering = ['-creado_en']

    def get_queryset(self):
        return Evento.objects.filter(organizador=self.request.user).select_related(
            'tipo', 'ubicacion', 'configuracion'
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return ListEventoSerializer
        return EventoSerializer

    def perform_create(self, serializer):
        serializer.save(organizador=self.request.user)


class EventoConfiguracionViewSet(viewsets.ModelViewSet):
    """Gestión de configuraciones de eventos del usuario autenticado."""
    serializer_class = ConfiguracionEventoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ConfiguracionEvento.objects.filter(
            evento__organizador=self.request.user
        ).select_related('evento')
