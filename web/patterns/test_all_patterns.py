import sys
sys.path.insert(0, '/app')

from web.patterns.singleton import ConfiguracionGlobal
from web.patterns.factory_method import ServiceFactory
from web.patterns.abstract_factory import EventFactoryProducer
from web.patterns.builder import EventoBodaBuilder, EventoConferenciaBuilder
from web.patterns.prototype import EventoPrototype, PrototypeEventos
from web.patterns.adapter import AdaptadorStripe, AdaptadorPayPal, AdaptadorCateringProveedorA
from web.patterns.decorator import DecoradorPremium, DecoradorFotografia
from web.patterns.facade import EventFacade
from web.patterns.composite import EventoCompuesto, EventoSimple
from web.patterns.proxy import EventProxyFactory
from web.patterns.bridge import BudgetReport, PDFFormatter
from web.patterns.strategy import EventFilter, FilterByBudget, CostCalculator, StandardCostCalculation
from web.patterns.observer import EventoObservable, AdminNotifier
from web.patterns.command import CommandInvoker, CreateEventCommand
from web.patterns.state import EventContext
from web.patterns.iterator import EventCollection
from web.patterns.memento import EventOriginator
from web.patterns.visitor import CateringEvent, CostCalculatorVisitor
from web.patterns.mediator import EventMediator, EventOrganizer, Vendor

def test_all_patterns():
    print("="*80)
    print("DESIGN PATTERNS TEST SUITE - BODAS PROJECT")
    print("="*80)
    print()

    tests_passed = 0
    tests_failed = 0

    try:
        print("1. Testing Singleton Pattern...")
        config = ConfiguracionGlobal()
        config2 = ConfiguracionGlobal()
        assert config is config2, "Singleton failed: different instances"
        print("   ✓ Singleton: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Singleton: FAIL - {e}")
        tests_failed += 1

    try:
        print("2. Testing Factory Method Pattern...")
        stripe = ServiceFactory.create_payment_provider('stripe')
        assert stripe is not None, "Factory failed: None returned"
        print("   ✓ Factory Method: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Factory Method: FAIL - {e}")
        tests_failed += 1

    try:
        print("3. Testing Abstract Factory Pattern...")
        components = EventFactoryProducer.create_event_components('wedding')
        assert 'invitation' in components, "Abstract Factory failed"
        print("   ✓ Abstract Factory: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Abstract Factory: FAIL - {e}")
        tests_failed += 1

    try:
        print("4. Testing Builder Pattern...")
        builder = EventoBodaBuilder()
        builder.set_nombre("Test Wedding")
        builder.set_max_asistentes(200)
        event = builder.build()
        assert event.nombre == "Test Wedding", "Builder failed"
        print("   ✓ Builder: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Builder: FAIL - {e}")
        tests_failed += 1

    try:
        print("5. Testing Prototype Pattern...")
        proto = EventoPrototype("EVT-001", "Wedding")
        cloned = proto.clonar()
        assert cloned.event_id != proto.event_id, "Prototype failed: same ID"
        print("   ✓ Prototype: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Prototype: FAIL - {e}")
        tests_failed += 1

    try:
        print("6. Testing Adapter Pattern...")
        adapter = AdaptadorStripe()
        result = adapter.procesar_pago(1000, "EUR")
        assert result['status'] == 'procesado', "Adapter failed"
        print("   ✓ Adapter: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Adapter: FAIL - {e}")
        tests_failed += 1

    try:
        print("7. Testing Decorator Pattern...")
        from web.patterns.decorator import EventoBase
        event = EventoBase("Test")
        decorated = DecoradorPremium(event)
        cost = decorated.obtener_costo()
        assert cost > 0, "Decorator failed: invalid cost"
        print("   ✓ Decorator: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Decorator: FAIL - {e}")
        tests_failed += 1

    try:
        print("8. Testing Facade Pattern...")
        facade = EventFacade()
        result = facade.create_complete_event(
            {"name": "Test", "budget": 1000},
            "stripe",
            ["Vendor"],
            "test@example.com"
        )
        assert result['success'], "Facade failed"
        print("   ✓ Facade: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Facade: FAIL - {e}")
        tests_failed += 1

    try:
        print("9. Testing Composite Pattern...")
        main = EventoCompuesto("Main Event")
        sub = EventoSimple("Sub Event", 1000)
        main.agregar_evento(sub)
        assert len(main.eventos) == 1, "Composite failed"
        print("   ✓ Composite: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ Composite: FAIL - {e}")
        tests_failed += 1

    try:
        print("10. Testing Proxy Pattern...")
        proxy = EventProxyFactory.create_guest_proxy("EVT-001")
        data = proxy.view()
        assert data is not None, "Proxy failed"
        print("    ✓ Proxy: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Proxy: FAIL - {e}")
        tests_failed += 1

    try:
        print("11. Testing Bridge Pattern...")
        formatter = PDFFormatter()
        report = BudgetReport(formatter)
        result = report.generate("EVT-001")
        assert result is not None, "Bridge failed"
        print("    ✓ Bridge: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Bridge: FAIL - {e}")
        tests_failed += 1

    try:
        print("12. Testing Strategy Pattern...")
        strategy = FilterByBudget()
        events = [{"budget": 5000}, {"budget": 15000}]
        filtered = strategy.filter(events, 10000)
        assert len(filtered) == 1, "Strategy failed"
        print("    ✓ Strategy: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Strategy: FAIL - {e}")
        tests_failed += 1

    try:
        print("13. Testing Observer Pattern...")
        event = EventoObservable("Test")
        observer = AdminNotifier()
        event.agregar_observador(observer)
        event.cambiar_estado("approved")
        print("    ✓ Observer: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Observer: FAIL - {e}")
        tests_failed += 1

    try:
        print("14. Testing Command Pattern...")
        invoker = CommandInvoker()
        cmd = CreateEventCommand("Wedding", "boda", "2024-06-15")
        invoker.execute_command(cmd)
        assert len(invoker.get_history()) > 0, "Command failed"
        print("    ✓ Command: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Command: FAIL - {e}")
        tests_failed += 1

    try:
        print("15. Testing State Pattern...")
        event = EventContext("EVT-001")
        event.approve()
        assert event.get_status() == "pending_approval", "State failed"
        print("    ✓ State: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ State: FAIL - {e}")
        tests_failed += 1

    try:
        print("16. Testing Iterator Pattern...")
        collection = EventCollection()
        collection.add_event({"name": "Event1"})
        collection.add_event({"name": "Event2"})
        count = 0
        for event in collection:
            count += 1
        assert count == 2, "Iterator failed"
        print("    ✓ Iterator: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Iterator: FAIL - {e}")
        tests_failed += 1

    try:
        print("17. Testing Memento Pattern...")
        event = EventOriginator("EVT-001")
        event.set_state(name="Wedding")
        checkpoint = event.save_checkpoint()
        event.set_state(name="Conference")
        event.restore_checkpoint(checkpoint)
        assert event._state["name"] == "Wedding", "Memento failed"
        print("    ✓ Memento: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Memento: FAIL - {e}")
        tests_failed += 1

    try:
        print("18. Testing Visitor Pattern...")
        catering = CateringEvent(guests=200)
        visitor = CostCalculatorVisitor()
        catering.accept(visitor)
        assert visitor.total_cost > 0, "Visitor failed"
        print("    ✓ Visitor: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Visitor: FAIL - {e}")
        tests_failed += 1

    try:
        print("19. Testing Mediator Pattern...")
        mediator = EventMediator()
        org = EventOrganizer("Organizer", mediator)
        vendor = Vendor("Vendor", mediator)
        mediator.register_colleague(org)
        mediator.register_colleague(vendor)
        org.send("Hello", "Vendor")
        assert len(mediator.get_message_log()) > 0, "Mediator failed"
        print("    ✓ Mediator: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Mediator: FAIL - {e}")
        tests_failed += 1

    try:
        print("20. Testing Template Method Pattern...")
        from web.patterns.template_method import crear_proceso_evento
        proceso = crear_proceso_evento("boda")
        assert proceso is not None, "Template Method failed"
        print("    ✓ Template Method: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Template Method: FAIL - {e}")
        tests_failed += 1

    try:
        print("21. Testing Chain of Responsibility Pattern...")
        from web.patterns.chain_of_responsibility import construir_cadena_completa, DatosValidacion
        chain = construir_cadena_completa()
        validation = DatosValidacion(
            nombre="Wedding",
            max_asistentes=150,
            capacidad_ubicacion=200,
            servicios_requeridos=["catering"],
            servicios_disponibles=["catering", "decoracion"],
            presupuesto_disponible=10000,
            costo_estimado=5000,
            fecha_inicio="2024-06-15",
            fecha_fin="2024-06-16"
        )
        result = chain.validar(validation)
        assert result is not None, "Chain of Responsibility failed"
        print("    ✓ Chain of Responsibility: PASS")
        tests_passed += 1
    except Exception as e:
        print(f"    ✗ Chain of Responsibility: FAIL - {e}")
        tests_failed += 1

    print()
    print("="*80)
    print(f"TEST RESULTS: {tests_passed} PASSED, {tests_failed} FAILED")
    print(f"SUCCESS RATE: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
    print("="*80)
    
    return tests_failed == 0

if __name__ == "__main__":
    success = test_all_patterns()
    sys.exit(0 if success else 1)
