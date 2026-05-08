from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict


class PasoEjecucion:

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.timestamp = datetime.now()
        self.estado = 'pendiente'
        self.resultado = {}

    def marcar_completado(self, resultado: dict = None):
        self.estado = 'completado'
        self.resultado = resultado or {}

    def marcar_error(self, error: str):
        self.estado = 'error'
        self.resultado = {'error': error}


class ProcesoEventoTemplate(ABC):

    def __init__(self, evento_django):
        self.evento = evento_django
        self.pasos_ejecutados: List[PasoEjecucion] = []

    def ejecutar_proceso(self) -> bool:
        try:
            if not self._ejecutar_paso('Validar datos', self.validar_datos):
                return False
            if not self._ejecutar_paso('Configurar servicios', self.configurar_servicios):
                return False
            if not self._ejecutar_paso('Calcular costes', self.calcular_costes):
                return False
            if not self._ejecutar_paso('Configuración específica', self.configurar_especifico):
                return False
            if not self._ejecutar_paso('Confirmar evento', self.confirmar_evento):
                return False
            return True
        except Exception as e:
            self._registrar_error(f"Error en proceso: {str(e)}")
            return False

    def _ejecutar_paso(self, nombre: str, funcion) -> bool:
        paso = PasoEjecucion(nombre)
        try:
            resultado = funcion()
            paso.marcar_completado(resultado)
        except Exception as e:
            paso.marcar_error(str(e))
            self.pasos_ejecutados.append(paso)
            return False
        finally:
            if paso not in self.pasos_ejecutados:
                self.pasos_ejecutados.append(paso)
        return True

    def _registrar_error(self, error: str):
        paso = PasoEjecucion("Error General")
        paso.marcar_error(error)
        self.pasos_ejecutados.append(paso)

                                                                                

    def validar_datos(self) -> dict:
        if not self.evento.nombre:
            raise ValueError("El evento debe tener nombre")
        if not self.evento.fecha_inicio:
            raise ValueError("El evento debe tener fecha de inicio")
        return {'datos_validados': True}

    def configurar_servicios(self) -> dict:
        servicios = []
        if self.evento.catering_contratado:
            servicios.append(self.evento.catering_contratado.nombre)
        if self.evento.streaming_contratado:
            servicios.append(self.evento.streaming_contratado.nombre)
        return {'servicios_configurados': servicios}

    def calcular_costes(self) -> dict:
        from .calculator import CalculadoraCostes

        costos = CalculadoraCostes.calcular_costo_total(self.evento)
        return {
            'costo_base': float(costos['presupuesto_limite']),
            'costo_adapter': float(costos['costo_adapter_total']),
            'costo_decorator': float(costos['costo_decorator_total']),
            'costo_total': float(costos['costos_totales']),
            'presupuesto_restante': float(costos['restante']),
            'desglose_completo': costos['desglose'],
        }

    @abstractmethod
    def configurar_especifico(self) -> dict:
        pass

    def confirmar_evento(self) -> dict:
        self.evento.confirmado = True
        self.evento.save(update_fields=['confirmado'])
        return {'evento_confirmado': True}

    def obtener_historial(self) -> List[Dict]:
        return [
            {
                'nombre': paso.nombre,
                'timestamp': paso.timestamp.isoformat(),
                'estado': paso.estado,
                'resultado': paso.resultado,
            }
            for paso in self.pasos_ejecutados
        ]


                                                                                

class ProcesoConferencia(ProcesoEventoTemplate):

    def configurar_especifico(self) -> dict:
        ponentes = self.evento.ponentes or []
        if not ponentes:
            raise ValueError("La conferencia debe tener al menos un ponente")
        return {'tipo': 'conferencia', 'ponentes_confirmados': True}


class ProcesoBoda(ProcesoEventoTemplate):

    def configurar_especifico(self) -> dict:
        if not self.evento.ceremonia_tipo:
            raise ValueError("Debe especificarse el tipo de ceremonia")
        return {'tipo': 'boda', 'ceremonia_confirmada': True}


class ProcesoConcierto(ProcesoEventoTemplate):

    def configurar_especifico(self) -> dict:
        artistas = self.evento.artistas or []
        if not artistas:
            raise ValueError("El concierto debe tener al menos un artista")
        return {'tipo': 'concierto', 'artistas_confirmados': True}


class ProcesoCumpleanos(ProcesoEventoTemplate):

    def configurar_especifico(self) -> dict:
        if not self.evento.edad_cumple or self.evento.edad_cumple < 1:
            raise ValueError("Debe especificarse la edad del cumpleaños")
        return {'tipo': 'cumpleaños', 'edad_especificada': True}


class ProcesoExposicion(ProcesoEventoTemplate):

    def configurar_especifico(self) -> dict:
        if not self.evento.cantidad_obras or self.evento.cantidad_obras < 1:
            raise ValueError("La exposición debe tener al menos una obra")
        return {'tipo': 'exposición', 'obras_confirmadas': True}


class ProcesoGenerico(ProcesoEventoTemplate):

    def configurar_especifico(self) -> dict:
        return {'tipo': 'genérico', 'configuracion_ok': True}


                                                                                

_PROCESOS = {
    'conferencia': ProcesoConferencia,
    'boda':        ProcesoBoda,
    'concierto':   ProcesoConcierto,
    'cumpleaños':  ProcesoCumpleanos,
    'exposición':  ProcesoExposicion,
}


def crear_proceso_evento(evento_django, tipo_evento: str) -> ProcesoEventoTemplate:
    ProcesoClass = _PROCESOS.get(tipo_evento.lower(), ProcesoGenerico)
    return ProcesoClass(evento_django)
