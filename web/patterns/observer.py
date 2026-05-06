from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class Observador(ABC):
    """Interfaz base para observadores"""

    @abstractmethod
    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        pass


class NotificadorEmail(Observador):
    """Notifica por email (simulado con log en consola)"""

    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        print(f"[EMAIL] Enviando email sobre cambio: {tipo_cambio}")
        print(f"        Evento: {evento.nombre}")
        print(f"        Detalles: {detalles}")


class NotificadorProveedor(Observador):
    """Notifica a proveedores (catering, streaming, etc.)"""

    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        print(f"[PROVEEDOR] Notificando proveedores sobre: {tipo_cambio}")
        print(f"            Evento: {evento.nombre}")
        if evento.catering_contratado:
            print(f"            → Catering: {evento.catering_contratado.nombre}")
        if evento.streaming_contratado:
            print(f"            → Streaming: {evento.streaming_contratado.nombre}")


class NotificadorAnalytica(Observador):
    """Registra eventos en el módulo de analítica"""

    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        print(f"[ANALÍTICA] Registrando evento: {tipo_cambio}")
        print(f"            Evento ID: {evento.id}")
        print(f"            Timestamp: {datetime.now().isoformat()}")


class EventoObservable:
    """Sujeto observable que notifica a observadores sobre cambios en el evento"""

    def __init__(self, evento_django):
        self.evento = evento_django
        self._observadores: List[Observador] = []

    def agregar_observador(self, observador: Observador):
        """Registra un nuevo observador"""
        if observador not in self._observadores:
            self._observadores.append(observador)

    def eliminar_observador(self, observador: Observador):
        """Desuscribe un observador"""
        if observador in self._observadores:
            self._observadores.remove(observador)

    def notificar(self, tipo_cambio: str, detalles: dict = None):
        """Notifica a todos los observadores suscritos"""
        if detalles is None:
            detalles = {}
        for observador in self._observadores:
            observador.actualizar(self.evento, tipo_cambio, detalles)

    def cambiar_fecha(self, nueva_fecha):
        """Cambia la fecha del evento y notifica"""
        fecha_anterior = self.evento.fecha_inicio
        self.evento.fecha_inicio = nueva_fecha
        self.evento.save()
        self.notificar(
            'evento_fecha_cambió',
            {
                'fecha_anterior': str(fecha_anterior),
                'fecha_nueva': str(nueva_fecha),
            }
        )

    def cambiar_estado(self, nuevo_estado):
        """Cambia el estado del evento y notifica"""
        self.notificar(
            'evento_estado_cambió',
            {'nuevo_estado': nuevo_estado}
        )

    def contratar_servicio(self, tipo_servicio: str, nombre_servicio: str):
        """Notifica cuando se contrata un servicio"""
        self.notificar(
            'servicio_contratado',
            {
                'tipo': tipo_servicio,
                'nombre': nombre_servicio,
            }
        )

    def registrar_pago(self, monto: float, pasarela: str):
        """Notifica cuando se procesa un pago"""
        self.notificar(
            'evento_pagado',
            {
                'monto': monto,
                'pasarela': pasarela,
            }
        )


def construir_observable_con_observadores(evento_django) -> EventoObservable:
    """
    Factory que crea un EventoObservable con todos los observadores
    estándar ya suscritos.
    """
    observable = EventoObservable(evento_django)
    observable.agregar_observador(NotificadorEmail())
    observable.agregar_observador(NotificadorProveedor())
    observable.agregar_observador(NotificadorAnalytica())
    return observable
