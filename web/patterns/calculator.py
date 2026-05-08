from decimal import Decimal

from .decorator import DECORADORES_DISPONIBLES


class CalculadoraCostes:
    """Calcula el coste total de un evento con presupuesto, adapters y decorators."""

    @staticmethod
    def calcular_costo_total(evento) -> dict:
        presupuesto_base = evento.obtener_presupuesto_efectivo()

        costo_catering = Decimal('0')
        if evento.catering_contratado:
            costo_catering = evento.catering_contratado.precio or Decimal('0')

        costo_streaming = Decimal('0')
        if evento.streaming_contratado:
            costo_streaming = evento.streaming_contratado.precio or Decimal('0')

        costo_adapter_total = costo_catering + costo_streaming
        costo_decorator_total = CalculadoraCostes._calcular_costo_decoradores(evento)
        costo_total = presupuesto_base + costo_adapter_total + costo_decorator_total

        return {
            'presupuesto_base': presupuesto_base,
            'costo_catering': costo_catering,
            'costo_streaming': costo_streaming,
            'costo_adapter_total': costo_adapter_total,
            'costo_decorator_total': costo_decorator_total,
            'costo_total': costo_total,
            'desglose': {
                'base': f"€{presupuesto_base:,.2f}",
                'catering': f"€{costo_catering:,.2f}",
                'streaming': f"€{costo_streaming:,.2f}",
                'extras': f"€{costo_decorator_total:,.2f}",
                'total': f"€{costo_total:,.2f}",
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
