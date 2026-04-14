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
# ReporteCompleto — PDF profesional con árbol jerárquico (reportlab)
# ---------------------------------------------------------------------------

class ReporteCompleto:
    """
    Genera un PDF profesional y detallado de un evento usando reportlab.
    Incluye información del evento, sub-eventos en árbol, servicios y resumen.
    No utiliza la abstracción Reporte/FormatoSalida: opera directamente sobre
    el modelo Django para acceder a la jerarquía de sub-eventos.
    """

    def generar_pdf(self, evento) -> bytes:
        """
        Recibe un modelo Evento de Django y devuelve los bytes del PDF generado.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable,
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            import io
            from django.utils import timezone as tz
        except ImportError:
            return self._generar_html_fallback(evento)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.HexColor('#1a1a2e'),
            alignment=TA_CENTER,
        )
        heading1 = ParagraphStyle(
            'Heading1Custom',
            parent=styles['Heading1'],
            fontSize=13,
            textColor=colors.HexColor('#5b5ef4'),
            spaceBefore=12,
            spaceAfter=4,
        )
        heading2 = ParagraphStyle(
            'Heading2Custom',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#2d2d6b'),
            spaceBefore=8,
            spaceAfter=2,
        )
        normal = ParagraphStyle(
            'NormalCustom',
            parent=styles['Normal'],
            fontSize=9,
            leading=14,
        )
        small_gray = ParagraphStyle(
            'SmallGray',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
        )
        tree_item = ParagraphStyle(
            'TreeItem',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=16,
            leading=13,
        )

        story = []

        # ── Header ──────────────────────────────────────────────────────────
        story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#5b5ef4')))
        story.append(Spacer(1, 6))
        story.append(Paragraph('REPORTE COMPLETO DEL EVENTO', title_style))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#5b5ef4')))
        story.append(Spacer(1, 12))

        # ── Event info ───────────────────────────────────────────────────────
        story.append(Paragraph(f'📅 {evento.nombre.upper()}', heading1))
        info_data = [
            ['Tipo:', str(evento.tipo) if evento.tipo else '—'],
            ['Fecha inicio:', evento.fecha_inicio.strftime('%d %b %Y · %H:%M') if evento.fecha_inicio else '—'],
            ['Fecha fin:', evento.fecha_fin.strftime('%d %b %Y · %H:%M') if evento.fecha_fin else '—'],
            ['Ubicación:', str(evento.ubicacion) if evento.ubicacion else '—'],
            ['Organizador:', evento.organizador.get_full_name() or evento.organizador.username],
            ['Máx. asistentes:', f'{evento.max_asistentes:,}'],
        ]
        if evento.descripcion:
            info_data.append(['Descripción:', evento.descripcion[:200]])

        t = Table(info_data, colWidths=[4 * cm, 13 * cm])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333366')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

        # ── Financial section ────────────────────────────────────────────────
        subeventos = list(evento.subeventos.all())
        if subeventos:
            story.append(Paragraph('💰 INFORMACIÓN FINANCIERA', heading1))
            fin_data = []
            total_presupuesto = 0.0
            for sub in subeventos:
                pres = float(sub.presupuesto or 0)
                total_presupuesto += pres
                fin_data.append([f'Presupuesto {sub.nombre}:', f'${pres:,.2f}'])
            if evento.presupuesto:
                total_presupuesto += float(evento.presupuesto)
            fin_data.append(['PRESUPUESTO TOTAL:', f'${total_presupuesto:,.2f}'])

            tf = Table(fin_data, colWidths=[10 * cm, 7 * cm])
            tf.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a6b1a')),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#5b5ef4')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(tf)
            story.append(Spacer(1, 10))

        # ── Sub-events tree ───────────────────────────────────────────────────
        if subeventos:
            story.append(Paragraph(f'🎵 SUB-EVENTOS ({len(subeventos)} total)', heading1))
            story.append(Spacer(1, 4))

            for idx, sub in enumerate(subeventos, 1):
                sub_cfg = getattr(sub, 'configuracion', None)

                # Sub-event header
                story.append(Paragraph(
                    f'  {idx}. {sub.nombre.upper()}',
                    heading2,
                ))

                # Calculate duration
                dur = ''
                if sub.fecha_inicio and sub.fecha_fin:
                    delta = sub.fecha_fin - sub.fecha_inicio
                    horas = delta.total_seconds() / 3600
                    dur = f'{horas:.1f}h'

                sub_data = [
                    ['├─ Tipo:', str(sub.tipo) if sub.tipo else '—'],
                    ['├─ Fechas:', (
                        f'{sub.fecha_inicio.strftime("%d %b %Y %H:%M")} – '
                        f'{sub.fecha_fin.strftime("%H:%M")} ({dur})'
                        if sub.fecha_inicio and sub.fecha_fin else '—'
                    )],
                    ['├─ Ubicación:', str(sub.ubicacion) if sub.ubicacion else str(evento.ubicacion) + ' (heredada)'],
                    ['├─ Capacidad:', f'{sub.max_asistentes:,} personas'],
                    ['└─ Presupuesto:', f'${float(sub.presupuesto or 0):,.2f}'],
                ]
                ts = Table(sub_data, colWidths=[4.5 * cm, 12.5 * cm])
                ts.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#5b5ef4')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 20),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('TOPPADDING', (0, 0), (-1, -1), 1),
                ]))
                story.append(ts)

                # Services
                if sub_cfg:
                    servicios_items = [
                        ('Catering',    sub_cfg.tiene_catering),
                        ('Escenario',   sub_cfg.tiene_escenario),
                        ('Iluminación', sub_cfg.tiene_iluminacion),
                        ('Seguridad',   sub_cfg.tiene_seguridad),
                        ('Streaming',   sub_cfg.tiene_streaming),
                        ('Decoración',  sub_cfg.tiene_decoracion),
                    ]
                    servicios_lines = []
                    for svc_nombre, svc_activo in servicios_items:
                        mark = '✓' if svc_activo else '✗'
                        color = '#1a6b1a' if svc_activo else '#999999'
                        servicios_lines.append(
                            f'<font color="{color}">   └─ {mark} {svc_nombre}</font>'
                        )
                    story.append(Paragraph(
                        '   Servicios Incluidos:', small_gray
                    ))
                    for line in servicios_lines:
                        story.append(Paragraph(line, tree_item))

                story.append(Spacer(1, 6))

        # ── Summary ────────────────────────────────────────────────────────────
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#cccccc')))
        story.append(Spacer(1, 6))
        story.append(Paragraph('📊 RESUMEN CONSOLIDADO', heading1))

        dur_total = evento.calcular_duracion_total()
        cap_max   = evento.obtener_capacidad_maxima()
        pres_total = evento.calcular_presupuesto_total()

        summary_data = [
            ['Total de Sub-eventos:', str(len(subeventos))],
            ['Duración Total:', f'{dur_total:.1f} horas'],
            ['Capacidad Máxima:', f'{cap_max:,} personas'],
            ['Presupuesto Total:', f'${pres_total:,.2f}'],
        ]
        tsum = Table(summary_data, colWidths=[6 * cm, 11 * cm])
        tsum.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333366')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(tsum)
        story.append(Spacer(1, 16))

        # ── Footer ────────────────────────────────────────────────────────────
        story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#5b5ef4')))
        story.append(Spacer(1, 4))
        now_str = tz.now().strftime('%d %b %Y %H:%M')
        story.append(Paragraph(
            f'Generado: {now_str} | Sistema de Gestión de Eventos',
            ParagraphStyle('Footer', parent=styles['Normal'],
                           fontSize=8, textColor=colors.HexColor('#888888'),
                           alignment=TA_CENTER),
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _generar_html_fallback(self, evento) -> bytes:
        """
        Genera un reporte HTML descargable cuando reportlab no está instalado.
        El navegador puede imprimirlo/guardarlo como PDF usando Ctrl+P → Guardar como PDF.
        Devuelve bytes UTF-8 del HTML generado.
        """
        from django.utils import timezone as tz

        now_str = tz.now().strftime('%d %b %Y %H:%M')
        fecha_inicio = evento.fecha_inicio.strftime('%d/%m/%Y %H:%M') if evento.fecha_inicio else '—'
        fecha_fin    = evento.fecha_fin.strftime('%d/%m/%Y %H:%M')    if evento.fecha_fin    else '—'
        presupuesto  = f'${evento.presupuesto:,.2f}' if evento.presupuesto else '—'
        organizador  = evento.organizador.username if evento.organizador else '—'
        ubicacion    = str(evento.ubicacion) if evento.ubicacion else '—'
        tipo         = str(evento.tipo)      if evento.tipo      else '—'
        descripcion  = evento.descripcion    if evento.descripcion else ''

        # Build services rows
        servicios_html = ''
        if hasattr(evento, 'configuracion') and evento.configuracion:
            c = evento.configuracion
            items = [
                ('🍽️ Catering',       c.tiene_catering),
                ('🎭 Escenario',       c.tiene_escenario),
                ('💡 Iluminación',     c.tiene_iluminacion),
                ('🔒 Seguridad',       c.tiene_seguridad),
                ('📡 Streaming',       c.tiene_streaming),
                ('🎨 Decoración',      c.tiene_decoracion),
            ]
            for nombre, activo in items:
                color  = '#1a6b1a' if activo else '#999'
                symbol = '✓' if activo else '✗'
                servicios_html += (
                    f'<tr><td>{nombre}</td>'
                    f'<td style="color:{color};font-weight:bold;">{symbol}</td></tr>'
                )

        # Build sub-events rows
        subeventos_html = ''
        for sub in evento.subeventos.all():
            sub_inicio = sub.fecha_inicio.strftime('%d/%m/%Y %H:%M') if sub.fecha_inicio else '—'
            sub_fin    = sub.fecha_fin.strftime('%d/%m/%Y %H:%M')    if sub.fecha_fin    else '—'
            sub_tipo   = str(sub.tipo)      if sub.tipo      else '—'
            sub_ub     = str(sub.ubicacion) if sub.ubicacion else '—'
            subeventos_html += (
                f'<tr>'
                f'<td>{sub.nombre}</td>'
                f'<td>{sub_tipo}</td>'
                f'<td>{sub_inicio}</td>'
                f'<td>{sub_fin}</td>'
                f'<td>{sub_ub}</td>'
                f'<td>{sub.max_asistentes}</td>'
                f'</tr>'
            )

        # Build optional sub-events section
        if evento.subeventos.exists():
            count = evento.subeventos.count()
            subeventos_section = (
                f'<h2>🌿 Sub-eventos ({count})</h2>'
                f'<table><thead><tr>'
                f'<th>Nombre</th><th>Tipo</th><th>Inicio</th>'
                f'<th>Fin</th><th>Ubicación</th><th>Asistentes</th>'
                f'</tr></thead>'
                f'<tbody>{subeventos_html}</tbody></table>'
            )
        else:
            subeventos_section = ''

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>Reporte: {evento.nombre}</title>
  <style>
    @page {{ margin: 2cm; }}
    body {{ font-family: Arial, sans-serif; font-size: 11pt; color: #1a1a2e; margin: 0; padding: 2em; }}
    h1 {{ font-size: 20pt; color: #5b5ef4; margin-bottom: .25em; }}
    h2 {{ font-size: 13pt; color: #2d2d6b; border-bottom: 2px solid #5b5ef4; padding-bottom: .2em; margin-top: 1.5em; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: .5em; }}
    th {{ background: #5b5ef4; color: #fff; padding: 6px 10px; text-align: left; font-size: 10pt; }}
    td {{ padding: 5px 10px; border-bottom: 1px solid #ddd; font-size: 10pt; }}
    tr:nth-child(even) td {{ background: #f5f5ff; }}
    .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: .4em 2em; margin-top: .5em; }}
    .meta-item {{ font-size: 10pt; }}
    .meta-item strong {{ color: #5b5ef4; }}
    .footer {{ margin-top: 2em; font-size: 8pt; color: #888; text-align: center; border-top: 1px solid #ddd; padding-top: .5em; }}
    .badge {{ display: inline-block; background: #5b5ef4; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 9pt; margin-left: 6px; }}
    .print-hint {{ background: #fffbe6; border: 1px solid #f0c040; padding: .5em 1em; border-radius: 6px; font-size: 9pt; margin-bottom: 1em; }}
    @media print {{ .print-hint {{ display: none; }} }}
  </style>
</head>
<body>
  <div class="print-hint">
    💡 Para guardar como PDF: usa <strong>Ctrl+P</strong> (o Archivo → Imprimir) y elige <em>Guardar como PDF</em>.
  </div>

  <h1>📋 Reporte Completo</h1>
  <h2 style="font-size:16pt;border:none;margin-top:.1em;">{evento.nombre} <span class="badge">{tipo}</span></h2>

  <h2>📌 Información General</h2>
  <div class="meta">
    <div class="meta-item"><strong>Organizador:</strong> {organizador}</div>
    <div class="meta-item"><strong>Ubicación:</strong> {ubicacion}</div>
    <div class="meta-item"><strong>Fecha inicio:</strong> {fecha_inicio}</div>
    <div class="meta-item"><strong>Fecha fin:</strong> {fecha_fin}</div>
    <div class="meta-item"><strong>Máx. asistentes:</strong> {evento.max_asistentes}</div>
    <div class="meta-item"><strong>Presupuesto:</strong> {presupuesto}</div>
  </div>
  {'<p style="margin-top:.75em;font-size:10pt;">' + descripcion + '</p>' if descripcion else ''}

  <h2>⚙️ Configuración de Servicios</h2>
  <table>
    <thead><tr><th>Servicio</th><th>Estado</th></tr></thead>
    <tbody>{servicios_html if servicios_html else '<tr><td colspan="2">Sin configuración disponible</td></tr>'}</tbody>
  </table>

  {subeventos_section}

  <div class="footer">Generado: {now_str} | Sistema de Gestión de Eventos</div>
</body>
</html>"""

        return html.encode('utf-8')


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
