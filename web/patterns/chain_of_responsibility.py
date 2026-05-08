
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List


                                                                             
                                             
                                                                             

@dataclass
class DatosValidacion:
    nombre: str = ""
    max_asistentes: int = 0
    capacidad_ubicacion: int = 0
    servicios_requeridos: List[str] = field(default_factory=list)
    servicios_disponibles: List[str] = field(default_factory=list)
    presupuesto_disponible: float = 0.0
    costo_estimado: float = 0.0
    fecha_inicio: Optional[object] = None                
    fecha_fin: Optional[object] = None                   
    eventos_existentes: List[dict] = field(default_factory=list)                   
    limite_global_asistentes: int = 5000
    modo_mantenimiento: bool = False
                                                                           
    exclude_evento_id: Optional[int] = None
                                               
    costo_catering: float = 0.0
    costo_streaming: float = 0.0
    catering_contratado: Optional[object] = None
    streaming_contratado: Optional[object] = None
    decoradores: List[str] = field(default_factory=list)


@dataclass
class ResultadoValidacion:
    aprobado: bool = True
    mensaje: str = ""
    validador: str = ""

    def __str__(self) -> str:
        if self.aprobado:
            return "✅ Evento aprobado — todos los validadores pasaron."
        return f"❌ Rechazado por [{self.validador}]: {self.mensaje}"


                                                                             
                   
                                                                             

class Handler(ABC):

    def __init__(self):
        self._siguiente: Optional[Handler] = None

    def set_siguiente(self, handler: 'Handler') -> 'Handler':
        self._siguiente = handler
        return handler

    @abstractmethod
    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:

    def _continuar(self, datos: DatosValidacion) -> ResultadoValidacion:
        if self._siguiente:
            return self._siguiente.manejar(datos)
        return ResultadoValidacion(aprobado=True)

    @property
    def nombre(self) -> str:
        return self.__class__.__name__


                                                                             
                       
                                                                             

class ValidadorCapacidad(Handler):

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        if datos.capacidad_ubicacion > 0 and datos.max_asistentes > datos.capacidad_ubicacion:
            return ResultadoValidacion(
                aprobado=False,
                mensaje=(
                    f"La ubicación solo admite {datos.capacidad_ubicacion} asistentes, "
                    f"pero se solicitaron {datos.max_asistentes}."
                ),
                validador=self.nombre,
            )
        return self._continuar(datos)


class ValidadorServicios(Handler):

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        no_disponibles = [
            s for s in datos.servicios_requeridos
            if s not in datos.servicios_disponibles
        ]
        if no_disponibles:
            return ResultadoValidacion(
                aprobado=False,
                mensaje=f"Servicios no disponibles: {', '.join(no_disponibles)}.",
                validador=self.nombre,
            )
        return self._continuar(datos)


class ValidadorServiciosExternos(Handler):

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        costo_catering = datos.costo_catering or 0
        costo_streaming = datos.costo_streaming or 0
        costo_total_servicios = costo_catering + costo_streaming

        if datos.presupuesto_disponible > 0 and costo_total_servicios > datos.presupuesto_disponible:
            exceso = costo_total_servicios - datos.presupuesto_disponible
            return ResultadoValidacion(
                aprobado=False,
                mensaje=(
                    f"El costo de servicios externos (Catering: €{costo_catering:,.2f} + "
                    f"Streaming: €{costo_streaming:,.2f} = €{costo_total_servicios:,.2f}) "
                    f"supera el presupuesto disponible (€{datos.presupuesto_disponible:,.2f}) "
                    f"en €{exceso:,.2f}."
                ),
                validador=self.nombre,
            )
        return self._continuar(datos)


class ValidadorPresupuesto(Handler):

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        from decimal import Decimal

        from web.models import Evento
        from web.patterns.calculator import CalculadoraCostes

        evento_temp = Evento(presupuesto=Decimal(str(datos.presupuesto_disponible or 0)))
        evento_temp.catering_contratado = datos.catering_contratado
        evento_temp.streaming_contratado = datos.streaming_contratado
        evento_temp.decoradores = datos.decoradores or []

        costos = CalculadoraCostes.calcular_costo_total(evento_temp)
        costo_total = float(costos['costos_totales'])
        costo_extras = float(costos['costo_adapter_total'] + costos['costo_decorator_total'])

        if datos.presupuesto_disponible > 0 and costo_extras > datos.presupuesto_disponible:
            exceso = costo_extras - datos.presupuesto_disponible
            return ResultadoValidacion(
                aprobado=False,
                mensaje=(
                    f"El costo total (€{costo_total:,.2f}) supera el presupuesto disponible "
                    f"(€{datos.presupuesto_disponible:,.2f}) en €{exceso:,.2f}. "
                    f"Desglose: Catering/Streaming €{float(costos['costo_adapter_total']):,.2f} + "
                    f"Extras €{float(costos['costo_decorator_total']):,.2f}. "
                    f"Restante: €{float(costos['restante']):,.2f}."
                ),
                validador=self.nombre,
            )
        return self._continuar(datos)


class ValidadorHorarios(Handler):

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        if datos.fecha_inicio is None or datos.fecha_fin is None:
            return self._continuar(datos)

        for evento in datos.eventos_existentes:
                                                                  
            if datos.exclude_evento_id is not None:
                if evento.get('id') == datos.exclude_evento_id:
                    continue

            inicio_existente = evento.get('inicio')
            fin_existente    = evento.get('fin')
            if inicio_existente is None or fin_existente is None:
                continue
                                                                                             
            if datos.fecha_inicio < fin_existente and datos.fecha_fin > inicio_existente:
                nombre_conflicto = evento.get('nombre', 'Evento desconocido')
                return ResultadoValidacion(
                    aprobado=False,
                    mensaje=(
                        f"Conflicto de horario con '{nombre_conflicto}' "
                        f"({inicio_existente} – {fin_existente})."
                    ),
                    validador=self.nombre,
                )
        return self._continuar(datos)


class ValidadorRestriccionesGlobales(Handler):

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        if datos.modo_mantenimiento:
            return ResultadoValidacion(
                aprobado=False,
                mensaje="La plataforma está en modo mantenimiento. No se pueden crear eventos.",
                validador=self.nombre,
            )

        if datos.max_asistentes > datos.limite_global_asistentes:
            return ResultadoValidacion(
                aprobado=False,
                mensaje=(
                    f"El número de asistentes ({datos.max_asistentes}) supera "
                    f"el límite global permitido ({datos.limite_global_asistentes})."
                ),
                validador=self.nombre,
            )
        return self._continuar(datos)


                                                                             
                                                       
                                                                             

def construir_cadena_completa() -> Handler:
    inicio = ValidadorCapacidad()
    inicio\
        .set_siguiente(ValidadorServicios())\
        .set_siguiente(ValidadorServiciosExternos())\
        .set_siguiente(ValidadorPresupuesto())\
        .set_siguiente(ValidadorHorarios())\
        .set_siguiente(ValidadorRestriccionesGlobales())
    return inicio


                                                                             
                                                                           
                                                                             

if __name__ == "__main__":
    from datetime import datetime

                                   
    datos_ok = DatosValidacion(
        nombre="Conferencia Tech",
        max_asistentes=200,
        capacidad_ubicacion=500,
        servicios_requeridos=["catering", "streaming"],
        servicios_disponibles=["catering", "streaming", "seguridad"],
        presupuesto_disponible=10_000,
        costo_estimado=8_500,
        fecha_inicio=datetime(2025, 6, 1, 9, 0),
        fecha_fin=datetime(2025, 6, 1, 18, 0),
        eventos_existentes=[],
        limite_global_asistentes=5000,
        modo_mantenimiento=False,
    )
    cadena = construir_cadena_completa()
    print(cadena.manejar(datos_ok))              

                                            
    datos_cap = DatosValidacion(
        nombre="Gran Concierto",
        max_asistentes=600,
        capacidad_ubicacion=500,
        limite_global_asistentes=5000,
    )
    print(construir_cadena_completa().manejar(datos_cap))               

                                        
    datos_mant = DatosValidacion(
        nombre="Evento bloqueado",
        max_asistentes=100,
        capacidad_ubicacion=300,
        modo_mantenimiento=True,
        limite_global_asistentes=5000,
    )
    print(construir_cadena_completa().manejar(datos_mant))                   
