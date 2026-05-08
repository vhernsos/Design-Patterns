from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class Observador(ABC):

    @abstractmethod
    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        pass


class NotificadorEmail(Observador):

    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        print(f"[EMAIL] Enviando email sobre cambio: {tipo_cambio}")
        print(f"        Evento: {evento.nombre}")
        print(f"        Detalles: {detalles}")


class NotificadorProveedor(Observador):

    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        if tipo_cambio == 'servicio_adapter_agregado':
            print(f"[PROVEEDOR] {detalles.get('tipo', '').upper()} agregado al evento {evento.nombre}")
            print(f"            Proveedor: {detalles.get('nombre')}")
            print(f"            Precio: €{detalles.get('precio', 0):,.2f}")
            print("            Se enviará notificación al proveedor...")
            return

        if tipo_cambio == 'servicio_adapter_removido':
            print(f"[PROVEEDOR] {detalles.get('tipo', '').upper()} removido del evento {evento.nombre}")
            print(f"            Proveedor afectado: {detalles.get('nombre')}")
            return

        if tipo_cambio == 'servicio_decorator_agregado':
            print(f"[PROVEEDOR] Extra agregado: {detalles.get('nombre')}")
            print(f"            Evento: {evento.nombre}")
            print(f"            Precio: €{detalles.get('precio', 0):,.2f}")
            return

        if tipo_cambio == 'servicio_decorator_removido':
            print(f"[PROVEEDOR] Extra removido: {detalles.get('nombre')}")
            print(f"            Evento: {evento.nombre}")
            return

        print(f"[PROVEEDOR] Notificando proveedores sobre: {tipo_cambio}")
        print(f"            Evento: {evento.nombre}")
        if evento.catering_contratado:
            print(f"            → Catering: {evento.catering_contratado.nombre}")
        if evento.streaming_contratado:
            print(f"            → Streaming: {evento.streaming_contratado.nombre}")


class NotificadorAnalytica(Observador):

    def actualizar(self, evento, tipo_cambio: str, detalles: dict):
        if 'servicio' in tipo_cambio or 'decorator' in tipo_cambio:
            print(f"[ANALÍTICA] Evento: {evento.id} - {evento.nombre}")
            print(f"            Cambio: {tipo_cambio}")
            print(f"            Detalles: {detalles}")
            print(f"            Timestamp: {datetime.now().isoformat()}")
            return

        print(f"[ANALÍTICA] Registrando evento: {tipo_cambio}")
        print(f"            Evento ID: {evento.id}")
        print(f"            Timestamp: {datetime.now().isoformat()}")


class EventoObservable:

    def __init__(self, evento_django):
        self.evento = evento_django
        self._observadores: List[Observador] = []

    def agregar_observador(self, observador: Observador):
        if observador not in self._observadores:
            self._observadores.append(observador)

    def eliminar_observador(self, observador: Observador):
        if observador in self._observadores:
            self._observadores.remove(observador)

    def notificar(self, tipo_cambio: str, detalles: dict = None):
        if detalles is None:
            detalles = {}
        for observador in self._observadores:
            observador.actualizar(self.evento, tipo_cambio, detalles)

    def cambiar_fecha(self, nueva_fecha):
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
        self.notificar(
            'evento_estado_cambió',
            {'nuevo_estado': nuevo_estado}
        )

    def contratar_servicio(self, tipo_servicio: str, nombre_servicio: str):
        self.agregar_servicio_adapter(tipo_servicio, nombre_servicio, 0)

    def agregar_servicio_adapter(self, tipo_servicio: str, nombre_servicio: str, precio: float):
        self.notificar(
            'servicio_adapter_agregado',
            {
                'tipo': tipo_servicio,
                'nombre': nombre_servicio,
                'precio': precio,
            }
        )

    def remover_servicio_adapter(self, tipo_servicio: str, nombre_servicio: str):
        self.notificar(
            'servicio_adapter_removido',
            {
                'tipo': tipo_servicio,
                'nombre': nombre_servicio,
            }
        )

    def agregar_decorador(self, nombre_decorador: str, precio: float):
        self.notificar(
            'servicio_decorator_agregado',
            {
                'nombre': nombre_decorador,
                'precio': precio,
            }
        )

    def remover_decorador(self, nombre_decorador: str):
        self.notificar(
            'servicio_decorator_removido',
            {
                'nombre': nombre_decorador,
            }
        )

    def registrar_pago(self, monto: float, pasarela: str):
        self.notificar(
            'evento_pagado',
            {
                'monto': monto,
                'pasarela': pasarela,
            }
        )


def construir_observable_con_observadores(evento_django) -> EventoObservable:
    observable = EventoObservable(evento_django)
    observable.agregar_observador(NotificadorEmail())
    observable.agregar_observador(NotificadorProveedor())
    observable.agregar_observador(NotificadorAnalytica())
    return observable
