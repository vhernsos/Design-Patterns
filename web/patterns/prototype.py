import copy


class EventoPrototype:

    def __init__(self, evento_db=None):
        if evento_db:
            self._load_from_db(evento_db)
        else:
            self.nombre        = ""
            self.tipo_id       = None
            self.ubicacion_id  = None
            self.fecha_inicio  = None
            self.fecha_fin     = None
            self.descripcion   = ""
            self.max_asistentes = 100
            self.presupuesto   = 0
            self.servicios_ids = []
            self.catering_contratado_id = None
            self.streaming_contratado_id = None
            self.decoradores = []
            self.tipo_evento = 'otro'
            self.ponentes = []
            self.ceremonia_tipo = ""
            self.artistas = []
            self.edad_cumple = None
            self.cantidad_obras = None
            self.config        = {}

    def _load_from_db(self, evento):
        self.nombre         = evento.nombre
        self.tipo_id        = evento.tipo_id
        self.ubicacion_id   = evento.ubicacion_id
        self.fecha_inicio   = evento.fecha_inicio
        self.fecha_fin      = evento.fecha_fin
        self.descripcion    = evento.descripcion
        self.max_asistentes = evento.max_asistentes
        self.presupuesto    = evento.presupuesto
        self.servicios_ids  = list(evento.servicios.values_list('id', flat=True))
        self.catering_contratado_id = evento.catering_contratado_id
        self.streaming_contratado_id = evento.streaming_contratado_id
        self.decoradores = list(evento.decoradores or [])
        self.tipo_evento = evento.tipo_evento
        self.ponentes = list(evento.ponentes or [])
        self.ceremonia_tipo = evento.ceremonia_tipo
        self.artistas = list(evento.artistas or [])
        self.edad_cumple = evento.edad_cumple
        self.cantidad_obras = evento.cantidad_obras
        if hasattr(evento, 'configuracion'):
            cfg = evento.configuracion
            self.config = {
                'tiene_catering':    cfg.tiene_catering,
                'tiene_escenario':   cfg.tiene_escenario,
                'tiene_iluminacion': cfg.tiene_iluminacion,
                'tiene_seguridad':   cfg.tiene_seguridad,
                'tiene_streaming':   cfg.tiene_streaming,
                'tiene_decoracion':  cfg.tiene_decoracion,
                'notas_adicionales': cfg.notas_adicionales,
            }
        else:
            self.config = {}

    def clonar(self) -> 'EventoPrototype':
        return copy.deepcopy(self)

    def set_nombre(self, nombre: str) -> 'EventoPrototype':
        self.nombre = nombre
        return self

    def set_fechas(self, inicio, fin) -> 'EventoPrototype':
        self.fecha_inicio = inicio
        self.fecha_fin    = fin
        return self

    def set_max_asistentes(self, cantidad: int) -> 'EventoPrototype':
        self.max_asistentes = cantidad
        return self

    def set_presupuesto(self, presupuesto) -> 'EventoPrototype':
        self.presupuesto = presupuesto
        return self

    def set_descripcion(self, descripcion: str) -> 'EventoPrototype':
        self.descripcion = descripcion
        return self

    def save_to_db(self, organizador):
        from web.models import Evento, ConfiguracionEvento                      

        evento = Evento.objects.create(
            nombre          = self.nombre,
            tipo_id         = self.tipo_id,
            ubicacion_id    = self.ubicacion_id,
            fecha_inicio    = self.fecha_inicio,
            fecha_fin       = self.fecha_fin,
            descripcion     = self.descripcion,
            max_asistentes  = self.max_asistentes,
            presupuesto     = self.presupuesto,
            organizador     = organizador,
            es_clon         = True,
            catering_contratado_id = self.catering_contratado_id,
            streaming_contratado_id = self.streaming_contratado_id,
            decoradores     = self.decoradores,
            tipo_evento     = self.tipo_evento,
            ponentes        = self.ponentes,
            ceremonia_tipo  = self.ceremonia_tipo,
            artistas        = self.artistas,
            edad_cumple     = self.edad_cumple,
            cantidad_obras  = self.cantidad_obras,
        )
        evento.servicios.set(self.servicios_ids)

        if self.config:
            ConfiguracionEvento.objects.create(evento=evento, **self.config)

        return evento

    def __str__(self):
        return (
            f"EventoPrototype(nombre={self.nombre}, "
            f"inicio={self.fecha_inicio}, fin={self.fecha_fin})"
        )


class PrototypeEventos:

    @staticmethod
    def clonar_evento(evento_original, organizador, **overrides):
        if evento_original.evento_padre_id is not None:
            raise ValueError(
                "No se pueden clonar subeventos. Solo se pueden clonar eventos principales."
            )
        if evento_original.es_clon:
            raise ValueError(
                "No se pueden clonar clones. Clona el evento original."
            )

        prototype = EventoPrototype(evento_original).clonar()
        PrototypeEventos._aplicar_overrides(prototype, overrides)
        nuevo_evento = prototype.save_to_db(organizador)
        nuevo_evento.evento_original = evento_original
        nuevo_evento.es_compuesto = evento_original.subeventos.exists()
        nuevo_evento.save(update_fields=['evento_original', 'es_compuesto'])

        PrototypeEventos._clonar_subeventos_recursivamente(
            evento_original,
            nuevo_evento,
            organizador,
        )
        return nuevo_evento

    @staticmethod
    def _aplicar_overrides(prototype, overrides):
        if overrides.get('nombre') is not None:
            prototype.set_nombre(overrides['nombre'])
        if overrides.get('fecha_inicio') is not None and overrides.get('fecha_fin') is not None:
            prototype.set_fechas(overrides['fecha_inicio'], overrides['fecha_fin'])
        if overrides.get('max_asistentes') is not None:
            prototype.set_max_asistentes(overrides['max_asistentes'])
        if overrides.get('descripcion') is not None:
            prototype.set_descripcion(overrides['descripcion'])
        if overrides.get('presupuesto') is not None:
            prototype.set_presupuesto(overrides['presupuesto'])

    @staticmethod
    def _clonar_subeventos_recursivamente(evento_original, evento_clon, organizador):
        for subevento in evento_original.subeventos.all():
            prototype = EventoPrototype(subevento).clonar()
            nuevo_subevento = prototype.save_to_db(organizador)
            nuevo_subevento.evento_padre = evento_clon
            nuevo_subevento.evento_original = subevento
            nuevo_subevento.es_compuesto = subevento.subeventos.exists()
            nuevo_subevento.save(update_fields=['evento_padre', 'evento_original', 'es_compuesto'])

            if subevento.subeventos.exists():
                PrototypeEventos._clonar_subeventos_recursivamente(
                    subevento,
                    nuevo_subevento,
                    organizador,
                )
