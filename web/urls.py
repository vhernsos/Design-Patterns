from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.dashboard,     name='dashboard'),
    path('events/<int:pk>/',          views.event_detail,  name='event_detail'),
    path('events/<int:pk>/edit/',     views.event_update,  name='event_update'),
    path('events/<int:pk>/delete/',   views.event_delete,  name='event_delete'),
    path('events/build/',             views.build_event,   name='build_event'),
    path('events/<int:pk>/clone/',    views.clone_event,   name='clone_event'),
    path('config/',                   views.global_config, name='global_config'),

    # Composite
    path('events/<int:pk>/subeventos/agregar/',
         views.agregar_subevento, name='agregar_subevento'),
    path('events/<int:evento_id>/subeventos/<int:subevento_id>/eliminar/',
         views.eliminar_subevento, name='eliminar_subevento'),

    # Bridge
    path('events/<int:pk>/reporte/<str:tipo>/<str:formato>/',
         views.generar_reporte, name='generar_reporte'),

    # Adapter
    path('events/<int:evento_id>/proveedores/',
         views.listar_proveedores, name='listar_proveedores'),
    path('events/<int:evento_id>/proveedores/<int:proveedor_id>/contratar/',
         views.contratar_servicio, name='contratar_servicio'),

    # Chain of Responsibility
    path('events/<int:pk>/validar/',
         views.validar_evento, name='validar_evento'),
]