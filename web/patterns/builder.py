from dataclasses import dataclass, field
from typing import List


@dataclass
class EventoData:
    nombre: str = ""
    tipo: str = ""
    ubicacion: str = ""
    fecha_inicio: str = ""
    fecha_fin: str = ""
    max_asistentes: int = 100
    descripcion: str = ""
    tiene_catering: bool = False
    tiene_escenario: bool = False
    tiene_iluminacion: bool = False
    tiene_seguridad: bool = False
    tiene_streaming: bool = False
    tiene_decoracion: bool = False
    servicios_adicionales: List[str] = field(default_factory=list)

    def __str__(self):
        servicios = []
        if self.tiene_catering:   servicios.append("Catering")
        if self.tiene_escenario:  servicios.append("Stage")
        if self.tiene_iluminacion: servicios.append("Lighting")
        if self.tiene_seguridad:  servicios.append("Security")
        if self.tiene_streaming:  servicios.append("Streaming")
        if self.tiene_decoracion: servicios.append("Decoration")
        servicios += self.servicios_adicionales
        return (
            f"Event: {self.nombre} | Type: {self.tipo} | "
            f"Location: {self.ubicacion} | "
            f"Services: {', '.join(servicios) or 'None'}"
        )


class EventoBuilder:

    def __init__(self):
        self._evento = EventoData()

    def set_nombre(self, nombre: str) -> 'EventoBuilder':
        self._evento.nombre = nombre
        return self

    def set_tipo(self, tipo: str) -> 'EventoBuilder':
        self._evento.tipo = tipo
        return self

    def set_ubicacion(self, ubicacion: str) -> 'EventoBuilder':
        self._evento.ubicacion = ubicacion
        return self

    def set_fechas(self, inicio: str, fin: str) -> 'EventoBuilder':
        self._evento.fecha_inicio = inicio
        self._evento.fecha_fin = fin
        return self

    def set_max_asistentes(self, cantidad: int) -> 'EventoBuilder':
        self._evento.max_asistentes = cantidad
        return self

    def set_descripcion(self, descripcion: str) -> 'EventoBuilder':
        self._evento.descripcion = descripcion
        return self

    def agregar_catering(self) -> 'EventoBuilder':
        self._evento.tiene_catering = True
        return self

    def agregar_escenario(self) -> 'EventoBuilder':
        self._evento.tiene_escenario = True
        return self

    def agregar_iluminacion(self) -> 'EventoBuilder':
        self._evento.tiene_iluminacion = True
        return self

    def agregar_seguridad(self) -> 'EventoBuilder':
        self._evento.tiene_seguridad = True
        return self

    def agregar_streaming(self) -> 'EventoBuilder':
        self._evento.tiene_streaming = True
        return self

    def agregar_decoracion(self) -> 'EventoBuilder':
        self._evento.tiene_decoracion = True
        return self

    def agregar_servicio_adicional(self, servicio: str) -> 'EventoBuilder':
        self._evento.servicios_adicionales.append(servicio)
        return self

    def build(self) -> EventoData:
        return self._evento

    def reset(self):
        self._evento = EventoData()


class EventoConferenciaBuilder(EventoBuilder):

    def __init__(self):
        super().__init__()
        self._evento.tipo = 'Conferencia'

    def configuracion_estandar(self) -> 'EventoConferenciaBuilder':
        return (
            self
            .agregar_escenario()
            .agregar_iluminacion()
            .agregar_seguridad()
            .agregar_streaming()
        )

    def configuracion_completa(self) -> 'EventoConferenciaBuilder':
        return (
            self
            .configuracion_estandar()
            .agregar_catering()
            .agregar_decoracion()
        )


class EventoBodaBuilder(EventoBuilder):

    def __init__(self):
        super().__init__()
        self._evento.tipo = 'Boda'

    def configuracion_estandar(self) -> 'EventoBodaBuilder':
        return (
            self
            .agregar_catering()
            .agregar_decoracion()
            .agregar_iluminacion()
        )

    def configuracion_completa(self) -> 'EventoBodaBuilder':
        return (
            self
            .configuracion_estandar()
            .agregar_escenario()
            .agregar_seguridad()
            .agregar_streaming()
        )


class EventoConcertBuilder(EventoBuilder):

    def __init__(self):
        super().__init__()
        self._evento.tipo = 'Concierto'

    def configuracion_estandar(self) -> 'EventoConcertBuilder':
        return (
            self
            .agregar_escenario()
            .agregar_iluminacion()
            .agregar_seguridad()
            .agregar_streaming()
        )

    def configuracion_completa(self) -> 'EventoConcertBuilder':
        return (
            self
            .configuracion_estandar()
            .agregar_catering()
            .agregar_decoracion()
        )


class EventoTheatreBuilder(EventoBuilder):

    def __init__(self):
        super().__init__()
        self._evento.tipo = 'Teatro'

    def configuracion_estandar(self) -> 'EventoTheatreBuilder':
        return (
            self
            .agregar_escenario()
            .agregar_iluminacion()
            .agregar_seguridad()
        )

    def configuracion_completa(self) -> 'EventoTheatreBuilder':
        return (
            self
            .configuracion_estandar()
            .agregar_catering()
            .agregar_decoracion()
            .agregar_streaming()
        )


class DirectorEvento:

    def __init__(self, builder: EventoBuilder):
        self._builder = builder

    def set_builder(self, builder: EventoBuilder):
        self._builder = builder

    def construir_evento_minimo(self, nombre: str) -> EventoData:
        return (
            self._builder
            .set_nombre(nombre)
            .agregar_seguridad()
            .build()
        )

    def construir_conferencia_completa(
        self, nombre: str, ubicacion: str,
        inicio: str, fin: str, asistentes: int = 200
    ) -> EventoData:
        if not isinstance(self._builder, EventoConferenciaBuilder):
            self._builder = EventoConferenciaBuilder()
        return (
            self._builder
            .set_nombre(nombre)
            .set_ubicacion(ubicacion)
            .set_fechas(inicio, fin)
            .set_max_asistentes(asistentes)
            .configuracion_completa()
            .build()
        )

    def construir_boda_sin_streaming(
        self, nombre: str, ubicacion: str,
        inicio: str, fin: str, asistentes: int = 150
    ) -> EventoData:
        if not isinstance(self._builder, EventoBodaBuilder):
            self._builder = EventoBodaBuilder()
        return (
            self._builder
            .set_nombre(nombre)
            .set_ubicacion(ubicacion)
            .set_fechas(inicio, fin)
            .set_max_asistentes(asistentes)
            .configuracion_estandar()
            .agregar_escenario()
            .agregar_seguridad()
            .build()
        )