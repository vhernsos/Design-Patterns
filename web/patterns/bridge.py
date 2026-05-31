from abc import ABC, abstractmethod
from datetime import datetime
import csv
from html import escape
from io import BytesIO
import json
from io import StringIO


class Reporte(ABC):
    def __init__(self, formato_salida):
        self._formato = formato_salida

    def cambiar_formato(self, formato_salida):
        self._formato = formato_salida

    @abstractmethod
    def generar(self, evento) -> str:
        pass

    def obtener_datos_basicos(self, evento) -> dict:
        return {
            'id': evento.id,
            'nombre': evento.nombre,
            'fecha': str(evento.fecha_inicio),
            'fecha_fin': str(evento.fecha_fin),
            'tipo': evento.tipo_evento,
            'tipo_modelo': str(evento.tipo) if evento.tipo else '',
            'ubicacion': str(evento.ubicacion) if evento.ubicacion else '',
        }


class ReporteResumen(Reporte):
    def generar(self, evento) -> str:
        datos = {
            **self.obtener_datos_basicos(evento),
            'descripcion': evento.descripcion,
            'organizador': evento.organizador.username,
            'asistentes': evento.max_asistentes,
        }
        return self._formato.renderizar(datos, 'resumen')


class ReporteDetallado(Reporte):
    def generar(self, evento) -> str:
        from web.patterns.calculator import CalculadoraCostes

        costos = CalculadoraCostes.calcular_costo_total(evento)

        datos = {
            **self.obtener_datos_basicos(evento),
            'descripcion': evento.descripcion,
            'organizador': evento.organizador.username,
            'asistentes': evento.max_asistentes,
            'catering': evento.catering_contratado.nombre if evento.catering_contratado else 'N/A',
            'streaming': evento.streaming_contratado.nombre if evento.streaming_contratado else 'N/A',
            'decoradores': evento.decoradores or [],
            'costos': costos,
            'subeventos': [
                {
                    'nombre': sub.nombre,
                    'tipo': str(sub.tipo) if sub.tipo else '',
                    'ubicacion': str(sub.ubicacion) if sub.ubicacion else '',
                    'fecha': str(sub.fecha_inicio),
                    'fecha_fin': str(sub.fecha_fin),
                    'asistentes': sub.max_asistentes,
                }
                for sub in evento.subeventos.all()
            ],
        }
        return self._formato.renderizar(datos, 'detallado')


class ReporteFinanciero(Reporte):
    def generar(self, evento) -> str:
        from web.patterns.calculator import CalculadoraCostes

        costos = CalculadoraCostes.calcular_costo_total(evento)

        datos = {
            **self.obtener_datos_basicos(evento),
            'presupuesto_limite': costos['presupuesto_limite'],
            'costos_totales': costos['costos_totales'],
            'restante': costos['restante'],
            'desglose': {
                'catering': costos['costo_catering'],
                'streaming': costos['costo_streaming'],
                'extras': costos['costo_decorator_total'],
            }
        }
        return self._formato.renderizar(datos, 'financiero')


class ReporteCompleto(Reporte):
    def generar(self, evento) -> str:
        from web.patterns.calculator import CalculadoraCostes

        costos = CalculadoraCostes.calcular_costo_total(evento)

        def obtener_subeventos(evento_padre):
            return [
                {
                    'nombre': sub.nombre,
                    'fecha': str(sub.fecha_inicio),
                    'asistentes': sub.max_asistentes,
                    'subeventos': obtener_subeventos(sub) if sub.subeventos.exists() else []
                }
                for sub in evento_padre.subeventos.all()
            ]

        datos = {
            **self.obtener_datos_basicos(evento),
            'descripcion': evento.descripcion,
            'organizador': evento.organizador.username,
            'costos': costos,
            'subeventos': obtener_subeventos(evento),
        }
        return self._formato.renderizar(datos, 'completo')


class FormatoSalida(ABC):
    @abstractmethod
    def renderizar(self, datos: dict, tipo_reporte: str) -> str:
        pass


class FormatoJSON(FormatoSalida):
    def renderizar(self, datos: dict, tipo_reporte: str) -> str:
        return json.dumps(datos, indent=2, default=str)


class FormatoCSV(FormatoSalida):
    def renderizar(self, datos: dict, tipo_reporte: str) -> str:
        if tipo_reporte == 'completo':
            raise ValueError('Formato CSV no soportado para reportes complejos')

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=datos.keys())
        writer.writeheader()
        writer.writerow(datos)
        return output.getvalue()


class FormatoHTML(FormatoSalida):
    def renderizar(self, datos: dict, tipo_reporte: str) -> str:
        return _render_professional_html(datos, tipo_reporte)


class FormatoPDF(FormatoSalida):
    def renderizar(self, datos: dict, tipo_reporte: str) -> bytes:
        return _render_pdf(datos, tipo_reporte)


class FormatoEmail(FormatoSalida):
    def renderizar(self, datos: dict, tipo_reporte: str) -> str:
        email = f"""
Asunto: Reporte - {datos.get('nombre', 'Evento')}

Estimado usuario,

Adjunto encontrará los detalles de su evento:

Evento: {datos.get('nombre')}
Fecha: {datos.get('fecha')}
Tipo: {datos.get('tipo')}

Para más detalles, visite el sistema.

Saludos,
Sistema de Gestión de Eventos
        """
        return email


def crear_reporte(tipo_reporte: str, formato_salida: str):
    reportes = {
        'resumen': ReporteResumen,
        'detallado': ReporteDetallado,
        'financiero': ReporteFinanciero,
        'completo': ReporteCompleto,
    }

    formatos = {
        'json': FormatoJSON,
        'csv': FormatoCSV,
        'html': FormatoHTML,
        'pdf': FormatoPDF,
        'email': FormatoEmail,
    }

    reporte_class = reportes.get(tipo_reporte.lower())
    formato_class = formatos.get(formato_salida.lower())

    if not reporte_class:
        raise ValueError(f'Tipo de reporte no soportado: {tipo_reporte}')
    if not formato_class:
        raise ValueError(f'Formato no soportado: {formato_salida}')

    formato = formato_class()
    return reporte_class(formato)


def _money(value):
    try:
        return f"EUR {float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _cost_rows(datos):
    costos = datos.get('costos') or {}
    desglose = datos.get('desglose') or {}
    rows = []
    if costos:
        rows = [
            ('Presupuesto', _money(costos.get('presupuesto_limite'))),
            ('Catering', _money(costos.get('costo_catering'))),
            ('Streaming', _money(costos.get('costo_streaming'))),
            ('Extras', _money(costos.get('costo_decorator_total'))),
            ('Costes totales', _money(costos.get('costos_totales'))),
            ('Restante', _money(costos.get('restante'))),
        ]
    elif desglose:
        rows = [(key.replace('_', ' ').title(), _money(value)) for key, value in desglose.items()]
        rows.insert(0, ('Presupuesto', _money(datos.get('presupuesto_limite'))))
        rows.append(('Costes totales', _money(datos.get('costos_totales'))))
        rows.append(('Restante', _money(datos.get('restante'))))
    return rows


def _render_professional_html(datos: dict, tipo_reporte: str) -> str:
    title = escape(datos.get('nombre') or 'Reporte de evento')
    generated = datetime.now().strftime('%d/%m/%Y %H:%M')
    cost_rows = _cost_rows(datos)
    subeventos = datos.get('subeventos') or []
    decoradores = datos.get('decoradores') or []

    def row(label, value):
        return f"<tr><th>{escape(label)}</th><td>{escape(str(value or 'N/A'))}</td></tr>"

    cost_html = ''.join(
        f"<tr><td>{escape(label)}</td><td class='num'>{escape(value)}</td></tr>"
        for label, value in cost_rows
    ) or "<tr><td colspan='2'>Sin datos financieros.</td></tr>"

    subevent_html = ''.join(
        "<tr>"
        f"<td>{escape(str(s.get('nombre', '')))}</td>"
        f"<td>{escape(str(s.get('tipo', '')))}</td>"
        f"<td>{escape(str(s.get('ubicacion', '')))}</td>"
        f"<td>{escape(str(s.get('fecha', '')))}</td>"
        f"<td class='num'>{escape(str(s.get('asistentes', '')))}</td>"
        "</tr>"
        for s in subeventos
    ) or "<tr><td colspan='5'>No hay sub-eventos registrados.</td></tr>"

    extras_html = ''.join(f"<span class='pill'>{escape(str(item))}</span>" for item in decoradores)
    if not extras_html:
        extras_html = "<span class='muted'>Sin extras contratados.</span>"

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    :root {{ --ink:#202238; --muted:#667085; --line:#e6e8f5; --brand:#5b5ef4; --green:#059669; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Arial, Helvetica, sans-serif; color:var(--ink); background:#f4f6ff; }}
    .page {{ max-width:1040px; margin:32px auto; background:white; border:1px solid var(--line); border-radius:14px; overflow:hidden; box-shadow:0 18px 45px rgba(32,34,56,.10); }}
    .hero {{ padding:34px 38px; color:white; background:linear-gradient(135deg,#4f46e5,#7c3aed 55%,#db2777); }}
    .eyebrow {{ text-transform:uppercase; letter-spacing:.08em; font-size:12px; opacity:.85; }}
    h1 {{ margin:8px 0 10px; font-size:34px; line-height:1.1; }}
    .hero p {{ margin:0; opacity:.9; }}
    .content {{ padding:30px 38px 38px; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
    .panel {{ border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff; }}
    .panel h2 {{ margin:0; padding:14px 18px; font-size:15px; background:#f7f8ff; border-bottom:1px solid var(--line); color:#3b3e66; }}
    table {{ width:100%; border-collapse:collapse; }}
    th, td {{ padding:12px 14px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th {{ width:34%; color:var(--muted); font-weight:600; }}
    .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
    .wide {{ grid-column:1 / -1; }}
    .pill {{ display:inline-block; margin:4px 6px 0 0; padding:6px 10px; border-radius:999px; background:#eef2ff; color:#4338ca; font-size:12px; font-weight:700; }}
    .muted {{ color:var(--muted); }}
    .footer {{ padding:16px 38px; background:#fbfcff; border-top:1px solid var(--line); color:var(--muted); font-size:12px; }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="eyebrow">Reporte {escape(tipo_reporte.title())}</div>
      <h1>{title}</h1>
      <p>Generado el {generated} mediante Bridge: tipo de reporte independiente del formato de salida.</p>
    </section>
    <section class="content">
      <div class="grid">
        <article class="panel">
          <h2>Datos del evento</h2>
          <table>
            {row('ID', datos.get('id'))}
            {row('Tipo', datos.get('tipo_modelo') or datos.get('tipo'))}
            {row('Inicio', datos.get('fecha'))}
            {row('Fin', datos.get('fecha_fin'))}
            {row('Ubicacion', datos.get('ubicacion'))}
            {row('Organizador', datos.get('organizador'))}
            {row('Asistentes', datos.get('asistentes'))}
          </table>
        </article>
        <article class="panel">
          <h2>Costes</h2>
          <table>{cost_html}</table>
        </article>
        <article class="panel wide">
          <h2>Descripcion y extras</h2>
          <table>
            {row('Descripcion', datos.get('descripcion'))}
            <tr><th>Extras</th><td>{extras_html}</td></tr>
            {row('Catering', datos.get('catering'))}
            {row('Streaming', datos.get('streaming'))}
          </table>
        </article>
        <article class="panel wide">
          <h2>Sub-eventos</h2>
          <table>
            <thead><tr><th>Nombre</th><th>Tipo</th><th>Ubicacion</th><th>Inicio</th><th class="num">Asistentes</th></tr></thead>
            <tbody>{subevent_html}</tbody>
          </table>
        </article>
      </div>
    </section>
    <footer class="footer">EventManager - Reporte generado por el patron Bridge.</footer>
  </main>
</body>
</html>"""


def _render_pdf(datos: dict, tipo_reporte: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title=datos.get('nombre') or 'Reporte',
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        textColor=colors.HexColor('#202238'),
        fontSize=22,
        leading=26,
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#4f46e5'),
        fontSize=13,
        leading=16,
        spaceBefore=14,
        spaceAfter=8,
    )
    normal = styles['BodyText']

    def p(value):
        return Paragraph(escape(str(value or 'N/A')), normal)

    elements = [
        Paragraph(datos.get('nombre') or 'Reporte de evento', title_style),
        Paragraph(f"Reporte {tipo_reporte} generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal),
        Spacer(1, 10),
    ]

    event_rows = [
        ['ID', p(datos.get('id'))],
        ['Tipo', p(datos.get('tipo_modelo') or datos.get('tipo'))],
        ['Inicio', p(datos.get('fecha'))],
        ['Fin', p(datos.get('fecha_fin'))],
        ['Ubicacion', p(datos.get('ubicacion'))],
        ['Organizador', p(datos.get('organizador'))],
        ['Asistentes', p(datos.get('asistentes'))],
        ['Descripcion', p(datos.get('descripcion'))],
    ]
    elements.append(Paragraph('Datos del evento', section_style))
    elements.append(_pdf_table(event_rows))

    elements.append(Paragraph('Costes', section_style))
    cost_rows = [[label, value] for label, value in _cost_rows(datos)] or [['Costes', 'Sin datos']]
    elements.append(_pdf_table(cost_rows))

    elements.append(Paragraph('Servicios y extras', section_style))
    extras = ', '.join(map(str, datos.get('decoradores') or [])) or 'Sin extras'
    service_rows = [
        ['Catering', p(datos.get('catering'))],
        ['Streaming', p(datos.get('streaming'))],
        ['Extras', p(extras)],
    ]
    elements.append(_pdf_table(service_rows))

    subeventos = datos.get('subeventos') or []
    elements.append(Paragraph('Sub-eventos', section_style))
    if subeventos:
        rows = [['Nombre', 'Tipo', 'Ubicacion', 'Inicio', 'Asistentes']]
        rows.extend([
            [
                p(sub.get('nombre')),
                p(sub.get('tipo')),
                p(sub.get('ubicacion')),
                p(sub.get('fecha')),
                str(sub.get('asistentes', '')),
            ]
            for sub in subeventos
        ])
        table = Table(rows, colWidths=[3.2 * cm, 2.4 * cm, 3.4 * cm, 4.2 * cm, 2.1 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef2ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#202238')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d9ddf2')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fbfcff')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph('No hay sub-eventos registrados.', normal))

    doc.build(elements)
    return buffer.getvalue()


def _pdf_table(rows):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle

    table = Table(rows, colWidths=[4.0 * cm, 11.5 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7f8ff')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4f46e5')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d9ddf2')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return table
