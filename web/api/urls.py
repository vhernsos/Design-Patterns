from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EventoViewSet, TipoEventoViewSet,
    UbicacionViewSet, EventoConfiguracionViewSet,
)

router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento-api')
router.register(r'tipos', TipoEventoViewSet, basename='tipo-api')
router.register(r'ubicaciones', UbicacionViewSet, basename='ubicacion-api')
router.register(r'configuraciones', EventoConfiguracionViewSet, basename='configuracion-api')

urlpatterns = [
    path('', include(router.urls)),
]
