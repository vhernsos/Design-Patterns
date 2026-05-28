from ..models import Evento
from ..patterns.chain_of_responsibility import DatosValidacion


def build_validation_data(evento_form_data, ubicacion_obj=None, config=None, exclude_evento_id=None) -> DatosValidacion:
    from ..patterns.singleton import ConfiguracionGlobal
    
    singleton = ConfiguracionGlobal()
    servicios_req = []
    cfg = evento_form_data
    
    for campo in ('tiene_catering', 'tiene_escenario', 'tiene_iluminacion',
                  'tiene_seguridad', 'tiene_streaming', 'tiene_decoracion'):
        if cfg.get(campo):
            servicios_req.append(campo.replace('tiene_', ''))

    capacidad_ub = ubicacion_obj.capacidad if ubicacion_obj else 0

    existentes = []
    if ubicacion_obj:
        qs = Evento.objects.filter(ubicacion=ubicacion_obj, evento_padre__isnull=True)
        for ev in qs:
            existentes.append({'id': ev.pk, 'nombre': ev.nombre, 'inicio': ev.fecha_inicio, 'fin': ev.fecha_fin})

    costo_catering = 0.0
    catering_obj = cfg.get('catering_contratado')
    if catering_obj:
        costo_catering = float(catering_obj.precio)

    costo_streaming = 0.0
    streaming_obj = cfg.get('streaming_contratado')
    if streaming_obj:
        costo_streaming = float(streaming_obj.precio)

    return DatosValidacion(
        nombre=cfg.get('nombre', ''),
        max_asistentes=cfg.get('max_asistentes', 0),
        capacidad_ubicacion=capacidad_ub,
        servicios_requeridos=servicios_req,
        servicios_disponibles=['catering', 'escenario', 'iluminacion', 'seguridad', 'streaming', 'decoracion'],
        presupuesto_disponible=float(cfg.get('presupuesto', 0) or 0),
        costo_estimado=0,
        fecha_inicio=cfg.get('fecha_inicio'),
        fecha_fin=cfg.get('fecha_fin'),
        eventos_existentes=existentes,
        limite_global_asistentes=singleton.get_limite_asistentes(),
        modo_mantenimiento=singleton.get_modo_mantenimiento(),
        exclude_evento_id=exclude_evento_id,
        costo_catering=costo_catering,
        costo_streaming=costo_streaming,
        catering_contratado=catering_obj,
        streaming_contratado=streaming_obj,
        decoradores=cfg.get('decoradores') or [],
    )
