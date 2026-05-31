from datetime import datetime, timedelta
from decimal import Decimal
import os
from types import SimpleNamespace

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from web.patterns.abstract_factory import EventFactoryProducer
from web.patterns.adapter import AdaptadorStripe, procesar_con_proveedor
from web.patterns.bridge import crear_reporte
from web.patterns.builder import DirectorEvento, EventoBodaBuilder
from web.patterns.chain_of_responsibility import DatosValidacion, construir_cadena_completa
from web.patterns.command import CommandInvoker, CreateEventCommand
from web.patterns.composite import EventoCompuesto, EventoSimple
from web.patterns.decorator import aplicar_decoradores
from web.patterns.facade import EventFacade
from web.patterns.factory_method import ServiceFactory
from web.patterns.iterator import EventCollection
from web.patterns.mediator import EventMediator, EventOrganizer, Vendor
from web.patterns.memento import EventOriginator
from web.patterns.observer import EventoObservable, NotificadorEmail
from web.patterns.prototype import EventoPrototype
from web.patterns.proxy import EventProxyFactory
from web.patterns.singleton import ConfiguracionGlobal
from web.patterns.state import EventContext
from web.patterns.strategy import CostCalculator, EventFilter, FilterByBudget, StandardCostCalculation
from web.patterns.template_method import crear_proceso_evento
from web.patterns.visitor import CateringEvent, CostCalculatorVisitor


class DemoEvento(SimpleNamespace):
    def obtener_presupuesto_efectivo(self):
        return self.presupuesto or Decimal("0")

    def save(self, update_fields=None):
        return None


def demo_evento():
    return DemoEvento(
        id=1,
        nombre="Boda Demo",
        descripcion="Celebracion completa",
        fecha_inicio=datetime(2026, 7, 18, 18, 0),
        fecha_fin=datetime(2026, 7, 19, 2, 0),
        presupuesto=Decimal("12000"),
        max_asistentes=150,
        tipo_evento="boda",
        organizador=SimpleNamespace(username="demo"),
        catering_contratado=None,
        streaming_contratado=None,
        decoradores=["dj_profesional", "fotografo"],
        confirmado=False,
        ponentes=[],
        ceremonia_tipo="civil",
        artistas=[],
        edad_cumple=None,
        cantidad_obras=None,
    )


def run_demo():
    print("DEMO DE PATRONES - PROYECTO BODAS")
    print("=" * 60)

    singleton_a = ConfiguracionGlobal()
    singleton_b = ConfiguracionGlobal()
    print(f"Singleton: misma instancia = {singleton_a is singleton_b}")

    payment = ServiceFactory.create_payment_provider("stripe").create_payment(2500, "EUR")
    print(f"Factory Method: proveedor = {payment['provider']}")

    components = EventFactoryProducer.create_event_components("wedding")
    print(f"Abstract Factory: invitacion = {components['invitation']}")

    boda = DirectorEvento(EventoBodaBuilder()).construir_boda_sin_streaming(
        "Boda Ana y Luis", "Finca Madrid", "2026-07-18 18:00", "2026-07-19 02:00"
    )
    print(f"Builder: {boda}")

    prototype = EventoPrototype().set_nombre("Evento base").set_max_asistentes(100)
    clone = prototype.clonar().set_nombre("Evento clonado")
    print(f"Prototype: original={prototype.nombre}, clon={clone.nombre}")

    adapter_result = procesar_con_proveedor(AdaptadorStripe(), {"monto": 500, "moneda": "EUR"})
    print(f"Adapter: pago exitoso = {adapter_result['exito']}")

    evento = demo_evento()
    decorado = aplicar_decoradores(evento, evento.decoradores)
    print(f"Decorator: precio con extras = {decorado.obtener_precio()}")

    facade = EventFacade().create_complete_event(
        {"name": "Boda Demo", "budget": 12000}, "stripe", ["Catering Co"], "demo@example.com"
    )
    print(f"Facade: pasos coordinados = {len(facade['steps'])}")

    programa = EventoCompuesto("Programa de boda")
    programa.agregar(EventoSimple("Ceremonia", 3000, 1.5, 150))
    programa.agregar(EventoSimple("Banquete", 9000, 5, 150))
    print(f"Composite: presupuesto total = {programa.calcular_presupuesto()}")

    proxy = EventProxyFactory.create_organizer_proxy("EVT-001")
    proxy.edit(name="Boda Demo", budget=12000)
    print(f"Proxy: presupuesto visible = {proxy.view_budget()}")

    reporte = crear_reporte("resumen", "json").generar(evento)
    print(f"Bridge: reporte JSON generado = {'Boda Demo' in reporte}")

    events = [{"name": "A", "budget": 5000}, {"name": "B", "budget": 15000}]
    filtered = EventFilter(FilterByBudget()).apply_filter(events, 10000)
    total = CostCalculator(StandardCostCalculation()).calculate_cost(1000, ["catering", "musica"])
    print(f"Strategy: filtrados={len(filtered)}, coste={total}")

    observable = EventoObservable(evento)
    observable.agregar_observador(NotificadorEmail())
    observable.notificar("evento_demo", {"estado": "ok"})
    print("Observer: notificacion enviada")

    invoker = CommandInvoker()
    invoker.execute_command(CreateEventCommand("Boda Demo", "boda", "2026-07-18"))
    print(f"Command: historial = {len(invoker.get_history())}")

    state = EventContext("EVT-001")
    state.approve()
    print(f"State: estado actual = {state.get_status()}")

    collection = EventCollection()
    collection.add_event("Ceremonia")
    collection.add_event("Banquete")
    print(f"Iterator: elementos = {', '.join(collection)}")

    originator = EventOriginator("EVT-001")
    originator.set_state(name="Boda Demo")
    checkpoint = originator.save_checkpoint()
    originator.set_state(name="Otro nombre")
    originator.restore_checkpoint(checkpoint)
    print(f"Memento: nombre restaurado = {originator.get_state()['name']}")

    visitor = CostCalculatorVisitor()
    CateringEvent(150).accept(visitor)
    print(f"Visitor: coste catering = {visitor.total_cost}")

    mediator = EventMediator()
    organizer = EventOrganizer("Organizador", mediator)
    vendor = Vendor("Catering", mediator)
    mediator.register_colleague(organizer)
    mediator.register_colleague(vendor)
    organizer.send("Confirmar menu", "Catering")
    print(f"Mediator: mensajes = {len(mediator.get_message_log())}")

    validation = DatosValidacion(
        nombre="Boda Demo",
        max_asistentes=150,
        capacidad_ubicacion=200,
        servicios_requeridos=["catering"],
        servicios_disponibles=["catering", "streaming"],
        presupuesto_disponible=12000,
        fecha_inicio=datetime.now() + timedelta(days=30),
        fecha_fin=datetime.now() + timedelta(days=30, hours=6),
    )
    result = construir_cadena_completa().manejar(validation)
    print(f"Chain of Responsibility: aprobado = {result.aprobado}")

    proceso = crear_proceso_evento(evento, "boda")
    print(f"Template Method: proceso ejecutado = {proceso.ejecutar_proceso()}")


if __name__ == "__main__":
    run_demo()
