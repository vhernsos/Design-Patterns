from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..forms import EventoUpdateForm, SubEventoForm
from ..models import (
    ConfiguracionEvento,
    Evento,
    HistorialNotificacion,
    ProveedorCatering,
    ProveedorStreaming,
    TipoEvento,
    Ubicacion,
)
from ..patterns.calculator import CalculadoraCostes
from ..patterns.prototype import PrototypeEventos
from ..patterns.template_method import crear_proceso_evento


class EventManagementRefactorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='secret123')
        self.other_user = User.objects.create_user(username='bob', password='secret123')
        self.tipo = TipoEvento.objects.create(nombre='Conferencia')
        self.ubicacion = Ubicacion.objects.create(
            nombre='Auditorio Central',
            direccion='Calle 1',
            ciudad='Madrid',
            capacidad=500,
        )
        self.catering = ProveedorCatering.objects.create(
            nombre='Premium Catering',
            precio=Decimal('250.00'),
        )
        self.streaming = ProveedorStreaming.objects.create(
            nombre='Streaming 4K',
            precio=Decimal('350.00'),
        )

    def _create_event(self, **kwargs):
        now = timezone.now()
        defaults = {
            'nombre': 'Evento Principal',
            'tipo': self.tipo,
            'ubicacion': self.ubicacion,
            'fecha_inicio': now,
            'fecha_fin': now + timedelta(hours=4),
            'descripcion': 'Evento de prueba',
            'max_asistentes': 120,
            'presupuesto': Decimal('1000.00'),
            'organizador': self.user,
            'tipo_evento': 'conferencia',
        }
        defaults.update(kwargs)
        return Evento.objects.create(**defaults)

    def test_prototype_service_clones_root_recursively_and_rejects_invalid_sources(self):
        evento = self._create_event(
            decoradores=['dj_profesional'],
            catering_contratado=self.catering,
            streaming_contratado=self.streaming,
            ponentes=['Ada Lovelace'],
        )
        ConfiguracionEvento.objects.create(
            evento=evento,
            tiene_catering=True,
            tiene_streaming=True,
        )
        subevento = self._create_event(
            nombre='Subevento',
            presupuesto=Decimal('0'),
            evento_padre=evento,
            es_compuesto=True,
        )
        ConfiguracionEvento.objects.create(evento=subevento, tiene_decoracion=True)
        nieto = self._create_event(
            nombre='Nieto',
            presupuesto=Decimal('0'),
            evento_padre=subevento,
        )
        ConfiguracionEvento.objects.create(evento=nieto, tiene_seguridad=True)

        clon = PrototypeEventos.clonar_evento(
            evento,
            self.user,
            nombre='Copia Evento Principal',
        )

        self.assertTrue(clon.es_clon)
        self.assertEqual(clon.evento_original, evento)
        self.assertEqual(clon.nombre, 'Copia Evento Principal')
        self.assertEqual(clon.presupuesto, evento.presupuesto)
        self.assertEqual(clon.catering_contratado, self.catering)
        self.assertEqual(clon.streaming_contratado, self.streaming)
        self.assertEqual(clon.decoradores, ['dj_profesional'])
        self.assertEqual(clon.subeventos.count(), 1)

        subevento_clonado = clon.subeventos.get()
        self.assertEqual(subevento_clonado.evento_original, subevento)
        self.assertTrue(subevento_clonado.es_clon)
        self.assertEqual(subevento_clonado.subeventos.count(), 1)
        self.assertEqual(subevento_clonado.subeventos.get().evento_original, nieto)

        with self.assertRaisesMessage(ValueError, 'No se pueden clonar subeventos'):
            PrototypeEventos.clonar_evento(subevento, self.user)
        with self.assertRaisesMessage(ValueError, 'No se pueden clonar clones'):
            PrototypeEventos.clonar_evento(clon, self.user)

    def test_subevento_form_and_budget_rules_remove_independent_budget(self):
        evento = self._create_event()
        subevento = self._create_event(
            nombre='Subevento',
            presupuesto=Decimal('99.00'),
            evento_padre=evento,
        )

        self.assertNotIn('presupuesto', SubEventoForm.base_fields)
        self.assertEqual(subevento.obtener_presupuesto_efectivo(), Decimal('0'))
        with self.assertRaisesMessage(ValueError, 'Los subeventos no tienen presupuesto independiente'):
            subevento.calcular_presupuesto_total()

    def test_cost_calculator_and_template_method_include_decorators(self):
        evento = self._create_event(
            presupuesto=Decimal('1000.00'),
            catering_contratado=self.catering,
            streaming_contratado=self.streaming,
            decoradores=['dj_profesional', 'valet_parking'],
            ponentes=['Ada Lovelace'],
        )

        costos = CalculadoraCostes.calcular_costo_total(evento)
        self.assertEqual(costos['presupuesto_limite'], Decimal('1000.00'))
        self.assertEqual(costos['costo_adapter_total'], Decimal('600.00'))
        self.assertEqual(costos['costo_decorator_total'], Decimal('2300'))
        self.assertEqual(costos['costos_totales'], Decimal('2900.00'))
        self.assertEqual(costos['restante'], Decimal('-1900.00'))

        proceso = crear_proceso_evento(evento, evento.tipo_evento)
        datos_coste = proceso.calcular_costes()
        self.assertEqual(datos_coste['costo_base'], 1000.0)
        self.assertEqual(datos_coste['costo_adapter'], 600.0)
        self.assertEqual(datos_coste['costo_decorator'], 2300.0)
        self.assertEqual(datos_coste['costo_total'], 2900.0)
        self.assertEqual(datos_coste['presupuesto_restante'], -1900.0)

    def test_event_update_edits_budget_and_services_without_editing_decorators(self):
        self.client.login(username='alice', password='secret123')
        evento = self._create_event(presupuesto=Decimal('1200.00'))
        ConfiguracionEvento.objects.create(evento=evento, tiene_catering=False)
        evento.decoradores = ['dj_profesional']
        evento.save(update_fields=['decoradores'])

        response = self.client.post(
            reverse('event_update', args=[evento.pk]),
            {
                'nombre': 'Evento Actualizado',
                'descripcion': 'Ahora con extras',
                'max_asistentes': 150,
                'presupuesto': '2500.00',
                'catering_contratado': self.catering.pk,
                'streaming_contratado': self.streaming.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        evento.refresh_from_db()
        self.assertEqual(evento.nombre, 'Evento Actualizado')
        self.assertEqual(evento.presupuesto, Decimal('2500.00'))
        self.assertEqual(evento.catering_contratado, self.catering)
        self.assertEqual(evento.streaming_contratado, self.streaming)
        self.assertEqual(evento.decoradores, ['dj_profesional'])
        self.assertEqual(HistorialNotificacion.objects.filter(evento=evento, tipo='evento_actualizado').count(), 3)

    def test_event_update_form_does_not_include_decoradores(self):
        self.assertNotIn('decoradores', EventoUpdateForm.base_fields)

    def test_descargar_reporte_bridge_json(self):
        self.client.login(username='alice', password='secret123')
        evento = self._create_event(catering_contratado=self.catering)

        response = self.client.get(
            reverse('descargar_reporte', args=[evento.pk]),
            {'tipo': 'financiero', 'formato': 'json'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('presupuesto_limite', response.content.decode())

    def test_clone_view_blocks_subevents_and_root_detail_hides_clone_warning(self):
        self.client.login(username='alice', password='secret123')
        evento = self._create_event()
        subevento = self._create_event(nombre='Subevento', presupuesto=Decimal('0'), evento_padre=evento)

        response = self.client.get(reverse('clone_event', args=[subevento.pk]), follow=True)
        self.assertContains(response, 'No se pueden clonar subeventos. Clona el evento principal.')

        other_event = self._create_event(nombre='Ajeno', organizador=self.other_user)
        forbidden = self.client.get(reverse('clone_event', args=[other_event.pk]))
        self.assertEqual(forbidden.status_code, 404)
