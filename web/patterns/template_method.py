from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict


class PasoEjecucion:
    """Representa un paso ejecutado dentro del Template Method"""

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
    """
    Clase base abstracta para procesos de eventos.
    Define el esqueleto del algoritmo (Template Method).
    """

    def __init__(self, evento_django):
        self.evento = evento_django
        self.pasos_ejecutados: List[PasoEjecucion] = []

    def ejecutar_proceso(self) -> bool:
        """Método Template — define el flujo general invariable"""
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
        """Ejecuta un paso y registra su resultado"""
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

    # ── Pasos comunes a todos los tipos de evento ─────────────────────────────

    def validar_datos(self) -> dict:
        """Valida datos básicos del evento"""
        if not self.evento.nombre:
            raise ValueError("El evento debe tener nombre")
        if not self.evento.fecha_inicio:
            raise ValueError("El evento debe tener fecha de inicio")
        return {'datos_validados': True}

    def configurar_servicios(self) -> dict:
        """Configura los servicios generales del evento"""
        servicios = []
        if self.evento.catering_contratado:
            servicios.append(self.evento.catering_contratado.nombre)
        if self.evento.streaming_contratado:
            servicios.append(self.evento.streaming_contratado.nombre)
        return {'servicios_configurados': servicios}

    def calcular_costes(self) -> dict:
        """Calcula los costes totales del evento"""
        costo_base = float(self.evento.presupuesto or 0)
        costo_catering = float(self.evento.catering_contratado.precio) if self.evento.catering_contratado else 0
        costo_streaming = float(self.evento.streaming_contratado.precio) if self.evento.streaming_contratado else 0
        costo_total = costo_base + costo_catering + costo_streaming
        return {
            'costo_base': costo_base,
            'costo_catering': costo_catering,
            'costo_streaming': costo_streaming,
            'costo_total': costo_total,
        }

    @abstractmethod
    def configurar_especifico(self) -> dict:
        """Paso personalizado que cada subclase debe implementar"""
        pass

    def confirmar_evento(self) -> dict:
        """Confirma el evento y persiste el cambio"""
        self.evento.confirmado = True
        self.evento.save(update_fields=['confirmado'])
        return {'evento_confirmado': True}

    def obtener_historial(self) -> List[Dict]:
        """Retorna el historial de pasos ejecutados"""
        return [
            {
                'nombre': paso.nombre,
                'timestamp': paso.timestamp.isoformat(),
                'estado': paso.estado,
                'resultado': paso.resultado,
            }
            for paso in self.pasos_ejecutados
        ]


# ── Implementaciones específicas por tipo de evento ───────────────────────────

class ProcesoConferencia(ProcesoEventoTemplate):
    """Flujo específico para conferencias"""

    def configurar_especifico(self) -> dict:
        ponentes = self.evento.ponentes or []
        if not ponentes:
            raise ValueError("La conferencia debe tener al menos un ponente")
        return {'tipo': 'conferencia', 'ponentes_confirmados': True}


class ProcesoBoda(ProcesoEventoTemplate):
    """Flujo específico para bodas"""

    def configurar_especifico(self) -> dict:
        if not self.evento.ceremonia_tipo:
            raise ValueError("Debe especificarse el tipo de ceremonia")
        return {'tipo': 'boda', 'ceremonia_confirmada': True}


class ProcesoConcierto(ProcesoEventoTemplate):
    """Flujo específico para conciertos"""

    def configurar_especifico(self) -> dict:
        artistas = self.evento.artistas or []
        if not artistas:
            raise ValueError("El concierto debe tener al menos un artista")
        return {'tipo': 'concierto', 'artistas_confirmados': True}


class ProcesoCumpleanos(ProcesoEventoTemplate):
    """Flujo específico para cumpleaños"""

    def configurar_especifico(self) -> dict:
        if not self.evento.edad_cumple or self.evento.edad_cumple < 1:
            raise ValueError("Debe especificarse la edad del cumpleaños")
        return {'tipo': 'cumpleaños', 'edad_especificada': True}


class ProcesoExposicion(ProcesoEventoTemplate):
    """Flujo específico para exposiciones"""

    def configurar_especifico(self) -> dict:
        if not self.evento.cantidad_obras or self.evento.cantidad_obras < 1:
            raise ValueError("La exposición debe tener al menos una obra")
        return {'tipo': 'exposición', 'obras_confirmadas': True}


class ProcesoGenerico(ProcesoEventoTemplate):
    """Flujo genérico para tipos de evento no especializados"""

    def configurar_especifico(self) -> dict:
        return {'tipo': 'genérico', 'configuracion_ok': True}


# ── Factory ───────────────────────────────────────────────────────────────────

_PROCESOS = {
    'conferencia': ProcesoConferencia,
    'boda':        ProcesoBoda,
    'concierto':   ProcesoConcierto,
    'cumpleaños':  ProcesoCumpleanos,
    'exposición':  ProcesoExposicion,
}


def crear_proceso_evento(evento_django, tipo_evento: str) -> ProcesoEventoTemplate:
    """
    Factory: crea el proceso correcto según el tipo de evento.
    Usa ProcesoGenerico como fallback para tipos no especializados.
    """
    ProcesoClass = _PROCESOS.get(tipo_evento.lower(), ProcesoGenerico)
    return ProcesoClass(evento_django)
