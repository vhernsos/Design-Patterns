"""
Chain of Responsibility Pattern — Cadena de Responsabilidad
===========================================================
Propósito:
    Validar y aprobar eventos antes de publicarlos o reservar recursos.
    Cada validador es independiente y responsable de una sola cosa.
    La cadena puede configurarse dinámicamente agregando o removiendo eslabones.

Estructura:
    Handler (abstracto)
        └── ValidadorCapacidad
        └── ValidadorServicios
        └── ValidadorPresupuesto
        └── ValidadorHorarios
        └── ValidadorRestriccionesGlobales

Uso típico:
    cadena = (
        ValidadorCapacidad()
        .set_siguiente(ValidadorServicios())
        .set_siguiente(ValidadorPresupuesto())
        .set_siguiente(ValidadorHorarios())
        .set_siguiente(ValidadorRestriccionesGlobales())
    )
    resultado = cadena.manejar(datos_evento)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List


# ---------------------------------------------------------------------------
# Objeto de datos: lo que viaja por la cadena
# ---------------------------------------------------------------------------

@dataclass
class DatosValidacion:
    """
    Contenedor con toda la información necesaria para validar un evento.
    Puede ampliarse sin modificar los validadores existentes.
    """
    nombre: str = ""
    max_asistentes: int = 0
    capacidad_ubicacion: int = 0
    servicios_requeridos: List[str] = field(default_factory=list)
    servicios_disponibles: List[str] = field(default_factory=list)
    presupuesto_disponible: float = 0.0
    costo_estimado: float = 0.0
    fecha_inicio: Optional[object] = None      # datetime
    fecha_fin: Optional[object] = None         # datetime
    eventos_existentes: List[dict] = field(default_factory=list)  # [{inicio, fin}]
    limite_global_asistentes: int = 5000
    modo_mantenimiento: bool = False
    # ID of the event being edited — excluded from schedule-conflict checks
    exclude_evento_id: Optional[int] = None


@dataclass
class ResultadoValidacion:
    """
    Resultado devuelto por la cadena de validación.

    Atributos:
        aprobado  : True si todos los validadores aceptaron el evento.
        mensaje   : Razón del rechazo (vacío si fue aprobado).
        validador : Nombre del validador que rechazó (vacío si fue aprobado).
    """
    aprobado: bool = True
    mensaje: str = ""
    validador: str = ""

    def __str__(self) -> str:
        if self.aprobado:
            return "✅ Evento aprobado — todos los validadores pasaron."
        return f"❌ Rechazado por [{self.validador}]: {self.mensaje}"


# ---------------------------------------------------------------------------
# Handler abstracto
# ---------------------------------------------------------------------------

class Handler(ABC):
    """
    Clase base abstracta para los eslabones de la cadena.

    Cada subclase implementa `validar()` con su lógica específica.
    Si la validación propia pasa, delega al siguiente eslabón con `_continuar()`.
    """

    def __init__(self):
        self._siguiente: Optional[Handler] = None

    def set_siguiente(self, handler: 'Handler') -> 'Handler':
        """
        Encadena el siguiente validador y lo devuelve para facilitar
        la construcción fluida de la cadena.

        Ejemplo:
            ValidadorA().set_siguiente(ValidadorB()).set_siguiente(ValidadorC())
        """
        self._siguiente = handler
        return handler

    @abstractmethod
    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        """
        Punto de entrada principal.  Debe:
        1. Ejecutar su propia validación.
        2. Devolver un ResultadoValidacion con aprobado=False si falla.
        3. Llamar a self._continuar(datos) si su validación pasa.
        """

    def _continuar(self, datos: DatosValidacion) -> ResultadoValidacion:
        """Delega al siguiente eslabón o aprueba si es el último."""
        if self._siguiente:
            return self._siguiente.manejar(datos)
        return ResultadoValidacion(aprobado=True)

    @property
    def nombre(self) -> str:
        """Nombre legible del validador (nombre de la clase)."""
        return self.__class__.__name__


# ---------------------------------------------------------------------------
# Validadores concretos
# ---------------------------------------------------------------------------

class ValidadorCapacidad(Handler):
    """
    Eslabón 1 — Capacidad de la ubicación.
    Comprueba que el número de asistentes no supere la capacidad del lugar.
    """

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
    """
    Eslabón 2 — Disponibilidad de servicios.
    Verifica que todos los servicios requeridos estén disponibles.
    """

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


class ValidadorPresupuesto(Handler):
    """
    Eslabón 3 — Presupuesto disponible.
    Rechaza el evento si el costo estimado supera el presupuesto asignado.
    """

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        if datos.presupuesto_disponible > 0 and datos.costo_estimado > datos.presupuesto_disponible:
            exceso = datos.costo_estimado - datos.presupuesto_disponible
            return ResultadoValidacion(
                aprobado=False,
                mensaje=(
                    f"El costo estimado (${datos.costo_estimado:,.2f}) supera el "
                    f"presupuesto disponible (${datos.presupuesto_disponible:,.2f}) "
                    f"en ${exceso:,.2f}."
                ),
                validador=self.nombre,
            )
        return self._continuar(datos)


class ValidadorHorarios(Handler):
    """
    Eslabón 4 — Conflictos de horario.
    Detecta si las fechas del nuevo evento se solapan con eventos existentes.
    Cada elemento de `datos.eventos_existentes` debe tener las claves
    'inicio' y 'fin' (objetos datetime comparables).
    Los eventos cuyo 'id' coincida con datos.exclude_evento_id se ignoran
    (evita que un evento se compare consigo mismo al editarlo).
    """

    def manejar(self, datos: DatosValidacion) -> ResultadoValidacion:
        if datos.fecha_inicio is None or datos.fecha_fin is None:
            return self._continuar(datos)

        for evento in datos.eventos_existentes:
            # Skip the event being edited to avoid self-comparison
            if datos.exclude_evento_id is not None:
                if evento.get('id') == datos.exclude_evento_id:
                    continue

            inicio_existente = evento.get('inicio')
            fin_existente    = evento.get('fin')
            if inicio_existente is None or fin_existente is None:
                continue
            # Solapamiento: los intervalos se cruzan si inicio_a < fin_b AND fin_a > inicio_b
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
    """
    Eslabón 5 — Restricciones globales de la plataforma.
    Comprueba el límite global de asistentes y el modo mantenimiento
    extraídos de la configuración global (Singleton).
    """

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


# ---------------------------------------------------------------------------
# Función de conveniencia: construir la cadena completa
# ---------------------------------------------------------------------------

def construir_cadena_completa() -> Handler:
    """
    Devuelve la cadena estándar de validación con todos los validadores
    en el orden recomendado:

        Capacidad → Servicios → Presupuesto → Horarios → Restricciones globales
    """
    inicio = ValidadorCapacidad()
    inicio \
        .set_siguiente(ValidadorServicios()) \
        .set_siguiente(ValidadorPresupuesto()) \
        .set_siguiente(ValidadorHorarios()) \
        .set_siguiente(ValidadorRestriccionesGlobales())
    return inicio


# ---------------------------------------------------------------------------
# Ejemplo de uso (ejecutar directamente: python chain_of_responsibility.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from datetime import datetime

    # --- Caso 1: evento válido ---
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
    print(cadena.manejar(datos_ok))  # ✅ Aprobado

    # --- Caso 2: capacidad insuficiente ---
    datos_cap = DatosValidacion(
        nombre="Gran Concierto",
        max_asistentes=600,
        capacidad_ubicacion=500,
        limite_global_asistentes=5000,
    )
    print(construir_cadena_completa().manejar(datos_cap))  # ❌ Capacidad

    # --- Caso 3: modo mantenimiento ---
    datos_mant = DatosValidacion(
        nombre="Evento bloqueado",
        max_asistentes=100,
        capacidad_ubicacion=300,
        modo_mantenimiento=True,
        limite_global_asistentes=5000,
    )
    print(construir_cadena_completa().manejar(datos_mant))  # ❌ Mantenimiento
