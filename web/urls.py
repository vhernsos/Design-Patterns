from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.dashboard,     name='dashboard'),
    path('events/<int:pk>/',          views.event_detail,  name='event_detail'),
    path('evento/<int:pk>/editar/',   views.event_update,  name='event_update'),
    path('events/<int:pk>/edit/',     views.event_update,  name='event_update_legacy'),
    path('events/<int:pk>/delete/',   views.event_delete,  name='event_delete'),
    path('events/build/',             views.build_event,   name='build_event'),
    path('events/<int:pk>/clone/',    views.clone_event,   name='clone_event'),
    path('config/',                   views.global_config, name='global_config'),

               
    path('events/<int:pk>/subeventos/agregar/',
         views.agregar_subevento, name='agregar_subevento'),
    path('events/<int:evento_id>/subeventos/<int:subevento_id>/eliminar/',
         views.eliminar_subevento, name='eliminar_subevento'),
    path('events/<int:evento_id>/subeventos/<int:subevento_id>/editar/',
         views.editar_subevento, name='editar_subevento'),

            
    path('events/<int:pk>/reporte/<str:tipo>/<str:formato>/',
         views.generar_reporte, name='generar_reporte'),
    path('evento/<int:pk>/descargar/',
         views.descargar_reporte, name='descargar_reporte'),
                                                       
    path('events/<int:pk>/reporte/pdf/',
         views.generar_reporte, {'tipo': 'completo', 'formato': 'pdf'},
         name='generar_pdf'),
                                     
    path('evento/<int:pk>/api/json/',
         views.evento_api_json, name='evento_api_json'),

             
    path('events/<int:evento_id>/proveedores/',
         views.listar_proveedores, name='listar_proveedores'),
    path('events/<int:evento_id>/proveedores/<int:proveedor_id>/contratar/',
         views.contratar_servicio, name='contratar_servicio'),

                             
    path('events/<int:pk>/validar/',
         views.validar_evento, name='validar_evento'),

                                    
    path('evento/<int:evento_id>/contratar-catering/<int:catering_id>/',
         views.contratar_catering, name='contratar_catering'),
    path('evento/<int:evento_id>/contratar-streaming/<int:streaming_id>/',
         views.contratar_streaming, name='contratar_streaming'),

                                       
    path('pagar/<int:evento_id>/',
         views.procesar_pago, name='procesar_pago'),
    path('historial-transacciones/',
         views.historial_transacciones, name='historial_transacciones'),
    path('transaccion/<int:transaccion_id>/',
         views.detalle_transaccion, name='detalle_transaccion'),

                       
    path('evento/<int:evento_id>/decorador/<str:decorador_key>/toggle/',
         views.toggle_decorador, name='toggle_decorador'),

                             
    path('events/<int:pk>/confirmar/',
         views.confirmar_evento, name='confirmar_evento'),

                                             
    path('events/<int:pk>/notificaciones/',
         views.historial_notificaciones, name='historial_notificaciones'),
]
