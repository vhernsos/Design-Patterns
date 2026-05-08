from abc import ABC, abstractmethod
from datetime import datetime
import csv
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
            'tipo': evento.tipo_evento,
        }


class ReporteResumen(Reporte):
    def generar(self, evento) -> str:
        datos = {
            **self.obtener_datos_basicos(evento),
            'descripcion': evento.descripcion,
            'organizador': evento.organizador.username,
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
        html = '<html><body>'
        html += f"<h1>{datos.get('nombre', 'Reporte')}</h1>"
        html += "<table border='1'>"

        for key, value in datos.items():
            if isinstance(value, dict):
                html += f"<tr><td colspan='2'><strong>{key}</strong></td></tr>"
                for k, v in value.items():
                    html += f"<tr><td>{k}</td><td>{v}</td></tr>"
            elif isinstance(value, list):
                html += f"<tr><td colspan='2'><strong>{key}</strong>: {', '.join(map(str, value))}</td></tr>"
            else:
                html += f"<tr><td>{key}</td><td>{value}</td></tr>"

        html += '</table></body></html>'
        return html


class FormatoPDF(FormatoSalida):
    def renderizar(self, datos: dict, tipo_reporte: str) -> str:
        contenido = '% PDF-1.4\n'
        contenido += f"Reporte: {datos.get('nombre', 'Sin nombre')}\n"
        contenido += f"Generado: {datetime.now().isoformat()}\n\n"

        for key, value in datos.items():
            if not isinstance(value, (dict, list)):
                contenido += f"{key}: {value}\n"

        return contenido


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
