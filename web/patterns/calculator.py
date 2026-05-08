from decimal import Decimal

from .decorator import DECORADORES_DISPONIBLES


class CalculadoraCostes:
    """Calcula el gasto del evento y el presupuesto restante."""

    @staticmethod
    def calcular_costo_total(evento) -> dict:
        presupuesto_limite = evento.obtener_presupuesto_efectivo()

        costo_catering = Decimal('0')
        if evento.catering_contratado:
            costo_catering = evento.catering_contratado.precio or Decimal('0')

        costo_streaming = Decimal('0')
        if evento.streaming_contratado:
            costo_streaming = evento.streaming_contratado.precio or Decimal('0')

        costo_adapter_total = costo_catering + costo_streaming
        costo_decorator_total = CalculadoraCostes._calcular_costo_decoradores(evento)
        costos_totales = costo_adapter_total + costo_decorator_total
        restante = presupuesto_limite - costos_totales

        return {
            'presupuesto_limite': presupuesto_limite,
            'costo_catering': costo_catering,
            'costo_streaming': costo_streaming,
            'costo_adapter_total': costo_adapter_total,
            'costo_decorator_total': costo_decorator_total,
            'costos_totales': costos_totales,
            'restante': restante,
            'presupuesto_base': presupuesto_limite,
            'costo_total': costos_totales,
            'desglose': {
                'presupuesto_limite': f"€{presupuesto_limite:,.2f}",
                'catering': f"€{costo_catering:,.2f}",
                'streaming': f"€{costo_streaming:,.2f}",
                'extras': f"€{costo_decorator_total:,.2f}",
                'costos_totales': f"€{costos_totales:,.2f}",
                'restante': f"€{restante:,.2f}",
                'base': f"€{presupuesto_limite:,.2f}",
                'total': f"€{costos_totales:,.2f}",
            },
        }

    @staticmethod
    def _calcular_costo_decoradores(evento) -> Decimal:
        total = Decimal('0')
        for decorador_key in (evento.decoradores or []):
            decorador_class = DECORADORES_DISPONIBLES.get(decorador_key)
            if decorador_class:
                total += decorador_class.PRECIO
        return total
