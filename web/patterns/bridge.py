"""
Bridge Pattern — Puente
=======================
Propósito:
    Generar reportes de eventos en diferentes formatos de forma desacoplada.
    Separar la *abstracción* (qué reporte generar) de la *implementación*
    (cómo se formatea la salida), permitiendo N×M combinaciones sin duplicar código.

Estructura:
    Abstracción (Reporte)                Implementación (Formato)
    ─────────────────────────────        ──────────────────────────
    Reporte                              FormatoSalida
      ├── ReporteResumen                   ├── FormatoPDF
      ├── ReporteDetallado                 ├── FormatoEmail
      └── ReporteFinanciero                ├── FormatoHTML
                                           └── FormatoCSV

Uso típico:
    reporte = ReporteResumen(formato=FormatoPDF())
    salida  = reporte.generar(evento)

    reporte.cambiar_formato(FormatoCSV())   # cambia en caliente sin recrear
    salida  = reporte.generar(evento)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List


# ---------------------------------------------------------------------------
# Datos de un evento que llegan al reporte
# ---------------------------------------------------------------------------

@dataclass
class EventoReporte:
    """
    DTO con la información de un evento que necesita un reporte.
    Se crea desde un modelo Evento de Django o manualmente para pruebas.
    """
    nombre: str = ""
    tipo: str = ""
    ubicacion: str = ""
    fecha_inicio: str = ""
    fecha_fin: str = ""
    max_asistentes: int = 0
    organizador: str = ""
    descripcion: str = ""
    servicios: List[str] = field(default_factory=list)
    presupuesto: float = 0.0
    ingresos: float = 0.0
    gastos: Dict[str, float] = field(default_factory=dict)
    tiene_catering: bool = False
    tiene_escenario: bool = False
    tiene_streaming: bool = False

    @classmethod
    def desde_modelo(cls, evento) -> 'EventoReporte':
        """
        Construye un EventoReporte a partir de un modelo Evento de Django.
        Uso: EventoReporte.desde_modelo(evento_db)
        """
        servicios = [str(s) for s in evento.servicios.all()]
        cfg = getattr(evento, 'configuracion', None)
        return cls(
            nombre=evento.nombre,
            tipo=str(evento.tipo) if evento.tipo else "",
            ubicacion=str(evento.ubicacion) if evento.ubicacion else "",
            fecha_inicio=str(evento.fecha_inicio),
            fecha_fin=str(evento.fecha_fin),
            max_asistentes=evento.max_asistentes,
            organizador=str(evento.organizador),
            descripcion=evento.descripcion,
            servicios=servicios,
            tiene_catering=cfg.tiene_catering if cfg else False,
            tiene_escenario=cfg.tiene_escenario if cfg else False,
            tiene_streaming=cfg.tiene_streaming if cfg else False,
        )


# ---------------------------------------------------------------------------
# Implementación: interfaz de formato de salida
# ---------------------------------------------------------------------------

class FormatoSalida(ABC):
    """
    Implementación base del puente.
    Define cómo se renderiza cualquier contenido.
    """

    @abstractmethod
    def renderizar_titulo(self, titulo: str) -> str:
        """Renderiza el título principal del documento."""

    @abstractmethod
    def renderizar_seccion(self, titulo: str, contenido: Dict[str, Any]) -> str:
        """Renderiza una sección con pares clave-valor."""

    @abstractmethod
    def renderizar_lista(self, titulo: str, items: List[str]) -> str:
        """Renderiza una lista de elementos."""

    @abstractmethod
    def renderizar_tabla(self, cabeceras: List[str], filas: List[List[str]]) -> str:
        """Renderiza una tabla con cabeceras y filas."""

    @abstractmethod
    def ensamblar(self, partes: List[str]) -> str:
        """Combina todas las partes en el documento final."""


# ---------------------------------------------------------------------------
# Implementaciones concretas de formato
# ---------------------------------------------------------------------------

class FormatoPDF(FormatoSalida):
    """
    Implementación: simula la estructura de un documento PDF.
    En producción se integraría con ReportLab, WeasyPrint, etc.
    """

    def renderizar_titulo(self, titulo: str) -> str:
        separador = "=" * 60
        return f"{separador}\n  {titulo.upper()}\n{separador}"

    def renderizar_seccion(self, titulo: str, contenido: Dict[str, Any]) -> str:
        lineas = [f"\n--- {titulo} ---"]
        for clave, valor in contenido.items():
            lineas.append(f"  {clave:<25} {valor}")
        return "\n".join(lineas)

    def renderizar_lista(self, titulo: str, items: List[str]) -> str:
        lineas = [f"\n--- {titulo} ---"]
        for item in items:
            lineas.append(f"  • {item}")
        return "\n".join(lineas)

    def renderizar_tabla(self, cabeceras: List[str], filas: List[List[str]]) -> str:
        ancho = 20
        sep = "+" + (("-" * ancho + "+") * len(cabeceras))
        fila_cab = "|" + "|".join(f" {h:<{ancho-1}}" for h in cabeceras) + "|"
        lineas = [sep, fila_cab, sep]
        for fila in filas:
            lineas.append("|" + "|".join(f" {c:<{ancho-1}}" for c in fila) + "|")
        lineas.append(sep)
        return "\n".join(lineas)

    def ensamblar(self, partes: List[str]) -> str:
        return "\n".join(partes) + "\n\n[Documento PDF generado]\n"


class FormatoEmail(FormatoSalida):
    """
    Implementación: formatea el reporte como cuerpo de un correo electrónico.
    """

    def renderizar_titulo(self, titulo: str) -> str:
        return f"Asunto: {titulo}\n{'─' * 50}"

    def renderizar_seccion(self, titulo: str, contenido: Dict[str, Any]) -> str:
        lineas = [f"\n► {titulo}"]
        for clave, valor in contenido.items():
            lineas.append(f"    {clave}: {valor}")
        return "\n".join(lineas)

    def renderizar_lista(self, titulo: str, items: List[str]) -> str:
        lineas = [f"\n► {titulo}"]
        for item in items:
            lineas.append(f"    - {item}")
        return "\n".join(lineas)

    def renderizar_tabla(self, cabeceras: List[str], filas: List[List[str]]) -> str:
        lineas = ["\n" + " | ".join(cabeceras)]
        lineas.append("-" * 40)
        for fila in filas:
            lineas.append(" | ".join(fila))
        return "\n".join(lineas)

    def ensamblar(self, partes: List[str]) -> str:
        cuerpo = "\n".join(partes)
        return f"{cuerpo}\n\n---\nEste correo fue generado automáticamente.\n"


class FormatoHTML(FormatoSalida):
    """
    Implementación: genera HTML que puede integrarse en las plantillas Django.
    """

    def renderizar_titulo(self, titulo: str) -> str:
        return f"<h1>{titulo}</h1>"

    def renderizar_seccion(self, titulo: str, contenido: Dict[str, Any]) -> str:
        filas = "".join(
            f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in contenido.items()
        )
        return f"<h2>{titulo}</h2><table>{filas}</table>"

    def renderizar_lista(self, titulo: str, items: List[str]) -> str:
        items_html = "".join(f"<li>{i}</li>" for i in items)
        return f"<h2>{titulo}</h2><ul>{items_html}</ul>"

    def renderizar_tabla(self, cabeceras: List[str], filas: List[List[str]]) -> str:
        ths = "".join(f"<th>{h}</th>" for h in cabeceras)
        trs = "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in fila) + "</tr>"
            for fila in filas
        )
        return f"<table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>"

    def ensamblar(self, partes: List[str]) -> str:
        cuerpo = "\n".join(partes)
        return (
            "<!DOCTYPE html><html><body>"
            f"{cuerpo}"
            "</body></html>"
        )


class FormatoCSV(FormatoSalida):
    """
    Implementación: genera texto CSV para importar en hojas de cálculo.
    """

    def renderizar_titulo(self, titulo: str) -> str:
        return f"# {titulo}"

    def renderizar_seccion(self, titulo: str, contenido: Dict[str, Any]) -> str:
        lineas = [f"# {titulo}", "Campo,Valor"]
        for clave, valor in contenido.items():
            lineas.append(f"{clave},{valor}")
        return "\n".join(lineas)

    def renderizar_lista(self, titulo: str, items: List[str]) -> str:
        lineas = [f"# {titulo}", "Item"]
        for item in items:
            lineas.append(item)
        return "\n".join(lineas)

    def renderizar_tabla(self, cabeceras: List[str], filas: List[List[str]]) -> str:
        lineas = [",".join(cabeceras)]
        for fila in filas:
            lineas.append(",".join(fila))
        return "\n".join(lineas)

    def ensamblar(self, partes: List[str]) -> str:
        return "\n\n".join(partes) + "\n"


# ---------------------------------------------------------------------------
# Abstracción: Reporte base (el puente)
# ---------------------------------------------------------------------------

class Reporte(ABC):
    """
    Abstracción base del puente.
    Contiene una referencia a la implementación (FormatoSalida) y
    delega todo el renderizado en ella.
    """

    def __init__(self, formato: FormatoSalida):
        self._formato = formato

    def cambiar_formato(self, formato: FormatoSalida) -> None:
        """Permite cambiar el formato en tiempo de ejecución sin recrear el reporte."""
        self._formato = formato

    @abstractmethod
    def generar(self, evento: EventoReporte) -> str:
        """
        Genera el reporte completo para el evento dado.
        La lógica (qué datos mostrar) es responsabilidad de la subclase;
        el renderizado es responsabilidad del formato inyectado.
        """

    @property
    def nombre_formato(self) -> str:
        return self._formato.__class__.__name__


# ---------------------------------------------------------------------------
# Abstracciones concretas (tipos de reporte)
# ---------------------------------------------------------------------------

class ReporteResumen(Reporte):
    """
    Reporte de resumen ejecutivo: datos esenciales del evento.
    Combinable con cualquier FormatoSalida.
    """

    def generar(self, evento: EventoReporte) -> str:
        fmt = self._formato
        partes = [
            fmt.renderizar_titulo(f"Resumen del Evento: {evento.nombre}"),
            fmt.renderizar_seccion("Información General", {
                "Nombre":        evento.nombre,
                "Tipo":          evento.tipo,
                "Ubicación":     evento.ubicacion,
                "Inicio":        evento.fecha_inicio,
                "Fin":           evento.fecha_fin,
                "Asistentes":    evento.max_asistentes,
                "Organizador":   evento.organizador,
            }),
            fmt.renderizar_lista("Servicios Incluidos", evento.servicios or ["Ninguno"]),
        ]
        return fmt.ensamblar(partes)


class ReporteDetallado(Reporte):
    """
    Reporte detallado: incluye descripción completa, configuración y servicios.
    """

    def generar(self, evento: EventoReporte) -> str:
        fmt = self._formato
        config = {
            "Catering":   "✔" if evento.tiene_catering  else "✘",
            "Escenario":  "✔" if evento.tiene_escenario  else "✘",
            "Streaming":  "✔" if evento.tiene_streaming  else "✘",
        }
        partes = [
            fmt.renderizar_titulo(f"Reporte Detallado: {evento.nombre}"),
            fmt.renderizar_seccion("Datos del Evento", {
                "Nombre":       evento.nombre,
                "Tipo":         evento.tipo,
                "Ubicación":    evento.ubicacion,
                "Fecha Inicio": evento.fecha_inicio,
                "Fecha Fin":    evento.fecha_fin,
                "Max. Asistentes": evento.max_asistentes,
                "Organizador":  evento.organizador,
            }),
            fmt.renderizar_seccion("Descripción", {"Detalle": evento.descripcion or "Sin descripción"}),
            fmt.renderizar_seccion("Configuración de Servicios", config),
            fmt.renderizar_lista("Servicios Contratados", evento.servicios or ["Ninguno"]),
        ]
        return fmt.ensamblar(partes)


class ReporteFinanciero(Reporte):
    """
    Reporte financiero: presupuesto, ingresos, gastos y balance.
    """

    def generar(self, evento: EventoReporte) -> str:
        fmt = self._formato
        balance = evento.ingresos - evento.presupuesto
        total_gastos = sum(evento.gastos.values())
        margen = evento.ingresos - total_gastos if evento.ingresos > 0 else 0

        partes = [
            fmt.renderizar_titulo(f"Reporte Financiero: {evento.nombre}"),
            fmt.renderizar_seccion("Resumen Financiero", {
                "Presupuesto":    f"${evento.presupuesto:,.2f}",
                "Ingresos":       f"${evento.ingresos:,.2f}",
                "Balance":        f"${balance:,.2f}",
                "Margen neto":    f"${margen:,.2f}",
            }),
            fmt.renderizar_tabla(
                ["Concepto", "Monto"],
                [[concepto, f"${monto:,.2f}"] for concepto, monto in evento.gastos.items()]
            ) if evento.gastos else fmt.renderizar_lista("Gastos", ["Sin gastos registrados"]),
        ]
        return fmt.ensamblar(partes)


# ---------------------------------------------------------------------------
# Ejemplo de uso (ejecutar directamente: python bridge.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    evento_ejemplo = EventoReporte(
        nombre="Conferencia Tech 2025",
        tipo="Conferencia",
        ubicacion="Centro de Convenciones Norte",
        fecha_inicio="2025-06-01 09:00",
        fecha_fin="2025-06-01 18:00",
        max_asistentes=300,
        organizador="Ana López",
        descripcion="Conferencia anual de tecnología e innovación.",
        servicios=["Catering", "Streaming", "Escenario", "Iluminación"],
        presupuesto=15_000.0,
        ingresos=18_000.0,
        gastos={"Catering": 4_000, "Escenario": 3_500, "Streaming": 2_000, "Marketing": 1_500},
        tiene_catering=True,
        tiene_escenario=True,
        tiene_streaming=True,
    )

    print("=" * 70)
    print("REPORTE RESUMEN — FORMATO PDF")
    print("=" * 70)
    print(ReporteResumen(FormatoPDF()).generar(evento_ejemplo))

    print("\n" + "=" * 70)
    print("REPORTE FINANCIERO — FORMATO CSV")
    print("=" * 70)
    print(ReporteFinanciero(FormatoCSV()).generar(evento_ejemplo))

    print("\n" + "=" * 70)
    print("REPORTE DETALLADO — FORMATO EMAIL")
    print("=" * 70)
    print(ReporteDetallado(FormatoEmail()).generar(evento_ejemplo))

    # Cambio de formato en caliente (sin recrear el reporte)
    print("\n" + "=" * 70)
    print("REPORTE RESUMEN — CAMBIANDO A HTML EN CALIENTE")
    print("=" * 70)
    reporte = ReporteResumen(FormatoPDF())
    reporte.cambiar_formato(FormatoHTML())
    print(reporte.generar(evento_ejemplo))
