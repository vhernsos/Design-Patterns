from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import json

from .models import Evento, TipoEvento, ConfiguracionEvento, GlobalConfig, Ubicacion, ProveedorServicio, ServicioContratado, Pasarela, Transaccion, ProveedorCatering, ProveedorStreaming
from .forms import (
    EventoForm, ConfiguracionEventoForm, GlobalConfigForm,
    BuildEventoForm, CloneEventoForm, SubEventoForm,
)
from .patterns.singleton import ConfiguracionGlobal
from .patterns.builder import (
    EventoConferenciaBuilder, EventoBodaBuilder,
    EventoConcertBuilder, EventoTheatreBuilder, DirectorEvento,
)
from .patterns.prototype import EventoPrototype
from .patterns.chain_of_responsibility import (
    DatosValidacion, construir_cadena_completa,
)
from .patterns.bridge import (
    EventoReporte,
    ReporteResumen, ReporteDetallado, ReporteFinanciero,
    ReporteCompleto, ReporteEventoJSON,
    FormatoPDF, FormatoCSV, FormatoHTML, FormatoEmail, FormatoJSON,
)
from .patterns.adapter import (
    AdaptadorCateringProveedorA, AdaptadorCateringProveedorB,
    AdaptadorStripe, AdaptadorPayPal, AdaptadorMercadoPago,
    AdaptadorYouTube, AdaptadorVimeo, AdaptadorFacebookLive,
    get_adapter_for_pasarela,
)


def is_staff(user):
    return user.is_staff


# ── Helpers ───────────────────────────────────────────────────────────────────

def _construir_datos_validacion(evento_form_data, ubicacion_obj=None, config=None,
                                exclude_evento_id=None) -> DatosValidacion:
    """
    Build DatosValidacion from form cleaned data for the Chain of Responsibility.
    Pass exclude_evento_id when editing an existing event to prevent self-comparison.
    """
    singleton = ConfiguracionGlobal()
    servicios_req = []
    cfg = evento_form_data
    for campo in ('tiene_catering', 'tiene_escenario', 'tiene_iluminacion',
                  'tiene_seguridad', 'tiene_streaming', 'tiene_decoracion'):
        if cfg.get(campo):
            servicios_req.append(campo.replace('tiene_', ''))

    capacidad_ub = ubicacion_obj.capacidad if ubicacion_obj else 0

    # Collect existing root events at same location to check schedule conflicts.
    # Sub-events (evento_padre IS NOT NULL) are excluded because they are nested
    # within their parent and intentionally share the same location/dates.
    existentes = []
    if ubicacion_obj:
        qs = Evento.objects.filter(ubicacion=ubicacion_obj, evento_padre__isnull=True)
        for ev in qs:
            existentes.append({'id': ev.pk, 'nombre': ev.nombre, 'inicio': ev.fecha_inicio, 'fin': ev.fecha_fin})

    # Catering and streaming costs from selected providers
    costo_catering = 0.0
    catering_obj = cfg.get('catering_contratado')
    if catering_obj:
        costo_catering = float(catering_obj.precio)

    costo_streaming = 0.0
    streaming_obj = cfg.get('streaming_contratado')
    if streaming_obj:
        costo_streaming = float(streaming_obj.precio)

    return DatosValidacion(
        nombre=cfg.get('nombre', ''),
        max_asistentes=cfg.get('max_asistentes', 0),
        capacidad_ubicacion=capacidad_ub,
        servicios_requeridos=servicios_req,
        servicios_disponibles=['catering', 'escenario', 'iluminacion', 'seguridad', 'streaming', 'decoracion'],
        presupuesto_disponible=float(cfg.get('presupuesto', 0) or 0),
        costo_estimado=0,
        fecha_inicio=cfg.get('fecha_inicio'),
        fecha_fin=cfg.get('fecha_fin'),
        eventos_existentes=existentes,
        limite_global_asistentes=singleton.get_limite_asistentes(),
        modo_mantenimiento=singleton.get_modo_mantenimiento(),
        exclude_evento_id=exclude_evento_id,
        costo_catering=costo_catering,
        costo_streaming=costo_streaming,
    )


# ── Dashboard ────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    # Only show root events — sub-events are visible inside their parent's detail page
    eventos = Evento.objects.select_related('tipo', 'ubicacion', 'organizador').filter(
        evento_padre__isnull=True
    )
    tipo_id = request.GET.get('tipo')
    fecha   = request.GET.get('fecha')
    if tipo_id:
        eventos = eventos.filter(tipo_id=tipo_id)
    if fecha:
        eventos = eventos.filter(fecha_inicio__date=fecha)

    config = ConfiguracionGlobal()
    tipos  = TipoEvento.objects.all()
    return render(request, 'web/dashboard.html', {
        'eventos': eventos,
        'tipos':   tipos,
        'config':  config,
    })


# ── Detail ───────────────────────────────────────────────────────────────────
@login_required
def event_detail(request, pk):
    from decimal import Decimal
    evento = get_object_or_404(
        Evento.objects
              .select_related('tipo', 'ubicacion', 'organizador', 'evento_padre',
                              'catering_contratado', 'streaming_contratado')
              .prefetch_related('servicios', 'clones', 'subeventos', 'servicios_contratados__proveedor'),
        pk=pk,
    )
    config = ConfiguracionGlobal()
    catererings = ProveedorCatering.objects.all()
    streamings = ProveedorStreaming.objects.all()
    pasarelas = Pasarela.objects.filter(activa=True)

    # Calculate total amount including contracted external services
    monto_total = evento.calcular_monto_total()
    if evento.catering_contratado:
        monto_total += evento.catering_contratado.precio or Decimal('0')
    if evento.streaming_contratado:
        monto_total += evento.streaming_contratado.precio or Decimal('0')

    return render(request, 'web/event_detail.html', {
        'evento': evento,
        'config': config,
        'catererings': catererings,
        'streamings': streamings,
        'pasarelas': pasarelas,
        'monto_total': monto_total,
    })


# ── Update ───────────────────────────────────────────────────────────────────
@login_required
def event_update(request, pk):
    evento     = get_object_or_404(Evento, pk=pk)
    config_obj, _ = ConfiguracionEvento.objects.get_or_create(evento=evento)

    if request.method == 'POST':
        form        = EventoForm(request.POST, instance=evento)
        config_form = ConfiguracionEventoForm(request.POST, instance=config_obj)
        if form.is_valid() and config_form.is_valid():
            # Sub-events are exempt from Chain of Responsibility validation
            if evento.evento_padre is not None:
                form.save()
                config_form.save()
                messages.success(request, f'Sub-evento "{evento.nombre}" actualizado exitosamente.')
                return redirect('event_detail', pk=evento.pk)

            # ── Chain of Responsibility: validate before saving ───────────
            ubicacion_obj = form.cleaned_data.get('ubicacion')
            merged = {**form.cleaned_data, **config_form.cleaned_data}
            datos_validacion = _construir_datos_validacion(
                merged, ubicacion_obj=ubicacion_obj, exclude_evento_id=evento.pk
            )
            resultado = construir_cadena_completa().manejar(datos_validacion)
            if not resultado.aprobado:
                messages.error(
                    request,
                    f'❌ Validación fallida [{resultado.validador}]: {resultado.mensaje}',
                )
            else:
                form.save()
                config_form.save()
                messages.success(request, f'Evento "{evento.nombre}" actualizado exitosamente.')
                return redirect('event_detail', pk=evento.pk)
    else:
        form        = EventoForm(instance=evento)
        config_form = ConfiguracionEventoForm(instance=config_obj)
    return render(request, 'web/event_form.html', {
        'form':        form,
        'config_form': config_form,
        'title':       'Editar Evento',
        'evento':      evento,
        'proveedores_catering':  ProveedorCatering.objects.all(),
        'proveedores_streaming': ProveedorStreaming.objects.all(),
    })


# ── Delete ───────────────────────────────────────────────────────────────────
@login_required
def event_delete(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        nombre = evento.nombre
        evento.delete()
        messages.success(request, f'Evento "{nombre}" eliminado.')
        return redirect('dashboard')
    return render(request, 'web/event_confirm_delete.html', {'evento': evento})


# ── Builder ──────────────────────────────────────────────────────────────────
@login_required
def build_event(request):
    all_events = Evento.objects.select_related(
        'tipo', 'ubicacion'
    ).prefetch_related('configuracion').order_by('-creado_en')

    # Serialize event data for JavaScript (clone source selection)
    events_json = []
    for ev in all_events:
        cfg = {}
        if hasattr(ev, 'configuracion'):
            c = ev.configuracion
            cfg = {
                'tiene_catering':    c.tiene_catering,
                'tiene_escenario':   c.tiene_escenario,
                'tiene_iluminacion': c.tiene_iluminacion,
                'tiene_seguridad':   c.tiene_seguridad,
                'tiene_streaming':   c.tiene_streaming,
                'tiene_decoracion':  c.tiene_decoracion,
            }
        events_json.append({
            'id':           ev.pk,
            'nombre':       ev.nombre,
            'tipo':         str(ev.tipo) if ev.tipo else '—',
            'fecha_inicio': ev.fecha_inicio.strftime('%b %d, %Y') if ev.fecha_inicio else '',
            'ubicacion':    str(ev.ubicacion) if ev.ubicacion else '',
            'config':       cfg,
        })

    if request.method == 'POST':
        form = BuildEventoForm(request.POST)
        if form.is_valid():
            data       = form.cleaned_data
            build_mode = data['build_mode']

            # ── Clone Mode ───────────────────────────────────────────────────
            if build_mode == 'from_clone':
                original  = get_object_or_404(Evento, pk=data['source_event_id'])
                prototype = EventoPrototype(original)
                clone     = prototype.clonar()

                clone.set_nombre(data['nombre'])
                clone.set_fechas(data['fecha_inicio'], data['fecha_fin'])
                clone.set_max_asistentes(data['max_asistentes'])
                clone.set_descripcion(data.get('descripcion', ''))

                clone.config = {
                    'tiene_catering':    data.get('tiene_catering', False),
                    'tiene_escenario':   data.get('tiene_escenario', False),
                    'tiene_iluminacion': data.get('tiene_iluminacion', False),
                    'tiene_seguridad':   data.get('tiene_seguridad', False),
                    'tiene_streaming':   data.get('tiene_streaming', False),
                    'tiene_decoracion':  data.get('tiene_decoracion', False),
                    'notas_adicionales': prototype.config.get('notas_adicionales', ''),
                }

                nuevo_evento = clone.save_to_db(request.user)
                nuevo_evento.evento_original = original
                nuevo_evento.save()
                messages.success(
                    request,
                    f'Evento clonado exitosamente como "{nuevo_evento.nombre}".'
                )
                return redirect('event_detail', pk=nuevo_evento.pk)

            # ── Scratch Mode ─────────────────────────────────────────────────
            tipo_builder  = data['tipo_builder']
            configuracion = data['configuracion']

            builder_map = {
                'conferencia': EventoConferenciaBuilder,
                'boda':        EventoBodaBuilder,
                'concierto':   EventoConcertBuilder,
                'teatro':      EventoTheatreBuilder,
            }
            builder  = builder_map.get(tipo_builder, EventoConferenciaBuilder)()
            director = DirectorEvento(builder)
            inicio_str = data['fecha_inicio'].strftime('%Y-%m-%d %H:%M')
            fin_str    = data['fecha_fin'].strftime('%Y-%m-%d %H:%M')

            if configuracion == 'estandar':
                builder.set_nombre(data['nombre'])
                builder.set_ubicacion(data.get('ubicacion', ''))
                builder.set_fechas(inicio_str, fin_str)
                builder.set_max_asistentes(data['max_asistentes'])
                builder.configuracion_estandar()
                evento_data = builder.build()

            elif configuracion == 'completa':
                builder.set_nombre(data['nombre'])
                builder.set_ubicacion(data.get('ubicacion', ''))
                builder.set_fechas(inicio_str, fin_str)
                builder.set_max_asistentes(data['max_asistentes'])
                builder.configuracion_completa()
                evento_data = builder.build()

            else:  # custom
                builder.set_nombre(data['nombre'])
                builder.set_ubicacion(data.get('ubicacion', ''))
                builder.set_fechas(inicio_str, fin_str)
                builder.set_max_asistentes(data['max_asistentes'])
                builder.set_descripcion(data.get('descripcion', ''))
                if data.get('tiene_catering'):    builder.agregar_catering()
                if data.get('tiene_escenario'):   builder.agregar_escenario()
                if data.get('tiene_iluminacion'): builder.agregar_iluminacion()
                if data.get('tiene_seguridad'):   builder.agregar_seguridad()
                if data.get('tiene_streaming'):   builder.agregar_streaming()
                if data.get('tiene_decoracion'):  builder.agregar_decoracion()
                evento_data = builder.build()

            # ── Persist to DB ────────────────────────────────────────────────
            tipo_obj, _ = TipoEvento.objects.get_or_create(nombre=evento_data.tipo)
            ubicacion_obj = None
            if evento_data.ubicacion:
                ubicacion_obj, _ = Ubicacion.objects.get_or_create(
                    nombre=evento_data.ubicacion,
                    defaults={'direccion': '', 'ciudad': ''},
                )

            # ── Chain of Responsibility: validate before saving ───────────────
            datos_validacion = _construir_datos_validacion(
                {
                    'nombre': evento_data.nombre,
                    'max_asistentes': evento_data.max_asistentes,
                    'fecha_inicio': data['fecha_inicio'],
                    'fecha_fin': data['fecha_fin'],
                    'tiene_catering':    evento_data.tiene_catering,
                    'tiene_escenario':   evento_data.tiene_escenario,
                    'tiene_iluminacion': evento_data.tiene_iluminacion,
                    'tiene_seguridad':   evento_data.tiene_seguridad,
                    'tiene_streaming':   evento_data.tiene_streaming,
                    'tiene_decoracion':  evento_data.tiene_decoracion,
                    'presupuesto': data.get('presupuesto', 0),
                    'catering_contratado': data.get('catering_contratado'),
                    'streaming_contratado': data.get('streaming_contratado'),
                },
                ubicacion_obj=ubicacion_obj,
            )
            resultado = construir_cadena_completa().manejar(datos_validacion)
            if not resultado.aprobado:
                messages.error(
                    request,
                    f'❌ Validación fallida [{resultado.validador}]: {resultado.mensaje}',
                )
                return render(request, 'web/build_event.html', {
                    'form':          form,
                    'all_events':    all_events,
                    'events_json':   json.dumps(events_json),
                    'services_list': [
                        ('Catering',    '🍽️', 'catering'),
                        ('Escenario',   '🎭', 'escenario'),
                        ('Iluminación', '💡', 'iluminacion'),
                        ('Seguridad',   '🔒', 'seguridad'),
                        ('Transmisión', '📡', 'streaming'),
                        ('Decoración',  '🎨', 'decoracion'),
                    ],
                    'proveedores_catering':  ProveedorCatering.objects.all(),
                    'proveedores_streaming': ProveedorStreaming.objects.all(),
                    'resultado_validacion': resultado,
                })

            evento = Evento.objects.create(
                nombre                = evento_data.nombre,
                tipo                  = tipo_obj,
                ubicacion             = ubicacion_obj,
                fecha_inicio          = data['fecha_inicio'],
                fecha_fin             = data['fecha_fin'],
                descripcion           = evento_data.descripcion,
                max_asistentes        = evento_data.max_asistentes,
                organizador           = request.user,
                catering_contratado   = data.get('catering_contratado'),
                streaming_contratado  = data.get('streaming_contratado'),
            )
            ConfiguracionEvento.objects.create(
                evento            = evento,
                tiene_catering    = evento_data.tiene_catering,
                tiene_escenario   = evento_data.tiene_escenario,
                tiene_iluminacion = evento_data.tiene_iluminacion,
                tiene_seguridad   = evento_data.tiene_seguridad,
                tiene_streaming   = evento_data.tiene_streaming,
                tiene_decoracion  = evento_data.tiene_decoracion,
            )

            # ── Inline Sub-events (Composite) ─────────────────────────────
            import re as _re
            from django.utils.dateparse import parse_datetime as _parse_dt
            # Find all submitted sub-event indices via form field names
            sub_indices = sorted({
                int(m.group(1))
                for key in request.POST
                for m in [_re.match(r'^subevento-(\d+)-nombre$', key)]
                if m
            })
            created_subeventos = 0
            for i in sub_indices:
                prefix = f'subevento-{i}'
                sub_nombre = request.POST.get(f'{prefix}-nombre', '').strip()
                if not sub_nombre:
                    continue
                sub_tipo_nombre   = request.POST.get(f'{prefix}-tipo', '').strip()
                sub_ubicacion_str = request.POST.get(f'{prefix}-ubicacion', '').strip()
                sub_fecha_inicio  = request.POST.get(f'{prefix}-fecha_inicio', '')
                sub_fecha_fin     = request.POST.get(f'{prefix}-fecha_fin', '')
                sub_max           = request.POST.get(f'{prefix}-max_asistentes', '50')
                sub_presupuesto   = request.POST.get(f'{prefix}-presupuesto', '0')

                sub_fi = _parse_dt(sub_fecha_inicio) or data['fecha_inicio']
                sub_ff = _parse_dt(sub_fecha_fin)    or data['fecha_fin']

                sub_tipo_obj = tipo_obj
                if sub_tipo_nombre:
                    sub_tipo_obj, _ = TipoEvento.objects.get_or_create(nombre=sub_tipo_nombre)

                # Inherit parent location if not specified
                sub_ubicacion_obj = ubicacion_obj
                if sub_ubicacion_str and sub_ubicacion_str != (str(ubicacion_obj) if ubicacion_obj else ''):
                    sub_ubicacion_obj, _ = Ubicacion.objects.get_or_create(
                        nombre=sub_ubicacion_str,
                        defaults={'direccion': '', 'ciudad': ''},
                    )

                try:
                    sub_max_int = int(sub_max)
                except (ValueError, TypeError):
                    sub_max_int = 50
                try:
                    sub_pres = float(sub_presupuesto)
                except (ValueError, TypeError):
                    sub_pres = 0.0

                subevento = Evento.objects.create(
                    nombre         = sub_nombre,
                    tipo           = sub_tipo_obj,
                    ubicacion      = sub_ubicacion_obj,
                    fecha_inicio   = sub_fi,
                    fecha_fin      = sub_ff,
                    max_asistentes = sub_max_int,
                    presupuesto    = sub_pres,
                    organizador    = request.user,
                    evento_padre   = evento,
                    es_compuesto   = False,
                )
                # Sub-event services
                ConfiguracionEvento.objects.create(
                    evento            = subevento,
                    tiene_catering    = bool(request.POST.get(f'{prefix}-tiene_catering')),
                    tiene_escenario   = bool(request.POST.get(f'{prefix}-tiene_escenario')),
                    tiene_iluminacion = bool(request.POST.get(f'{prefix}-tiene_iluminacion')),
                    tiene_seguridad   = bool(request.POST.get(f'{prefix}-tiene_seguridad')),
                    tiene_streaming   = bool(request.POST.get(f'{prefix}-tiene_streaming')),
                    tiene_decoracion  = bool(request.POST.get(f'{prefix}-tiene_decoracion')),
                )
                created_subeventos += 1

            if created_subeventos > 0:
                evento.es_compuesto = True
                evento.save(update_fields=['es_compuesto'])

            messages.success(request, f'✅ Evento "{evento.nombre}" construido y validado exitosamente.')
            return redirect('event_detail', pk=evento.pk)
    else:
        form = BuildEventoForm()

    return render(request, 'web/build_event.html', {
        'form':          form,
        'all_events':    all_events,
        'events_json':   json.dumps(events_json),
        'services_list': [
            ('Catering',    '🍽️', 'catering'),
            ('Escenario',   '🎭', 'escenario'),
            ('Iluminación', '💡', 'iluminacion'),
            ('Seguridad',   '🔒', 'seguridad'),
            ('Transmisión', '📡', 'streaming'),
            ('Decoración',  '🎨', 'decoracion'),
        ],
        'proveedores_catering':  ProveedorCatering.objects.all(),
        'proveedores_streaming': ProveedorStreaming.objects.all(),
    })


# ── Prototype / Clone ─────────────────────────────────────────────────────────
@login_required
def clone_event(request, pk):
    original  = get_object_or_404(Evento, pk=pk)
    prototype = EventoPrototype(original)

    if request.method == 'POST':
        form = CloneEventoForm(request.POST)
        if form.is_valid():
            data  = form.cleaned_data
            clone = prototype.clonar()
            clone.set_nombre(data['nombre'])
            clone.set_fechas(data['fecha_inicio'], data['fecha_fin'])
            clone.set_max_asistentes(data['max_asistentes'])
            clone.set_descripcion(data.get('descripcion', ''))
            nuevo_evento = clone.save_to_db(request.user)
            nuevo_evento.evento_original = original
            nuevo_evento.save()

            # Clone sub-events if the original has any
            for sub_evento in original.subeventos.all():
                sub_prototype = EventoPrototype(sub_evento)
                sub_clone = sub_prototype.clonar()
                sub_clone.set_nombre(f"Copia de {sub_evento.nombre}")
                sub_evento_clonado = sub_clone.save_to_db(request.user)
                sub_evento_clonado.evento_padre = nuevo_evento
                sub_evento_clonado.save()

            messages.success(
                request,
                f'Evento clonado exitosamente como "{nuevo_evento.nombre}".'
            )
            return redirect('event_detail', pk=nuevo_evento.pk)
    else:
        form = CloneEventoForm(initial={
            'nombre':        f"Copia de {original.nombre}",
            'fecha_inicio':  original.fecha_inicio,
            'fecha_fin':     original.fecha_fin,
            'descripcion':   original.descripcion,
            'max_asistentes': original.max_asistentes,
        })
    return render(request, 'web/clone_event.html', {
        'form':     form,
        'original': original,
    })


# ── Global Config (Singleton) ─────────────────────────────────────────────────
@login_required
@user_passes_test(is_staff)
def global_config(request):
    db_config = GlobalConfig.load()
    singleton = ConfiguracionGlobal()

    if request.method == 'POST':
        form = GlobalConfigForm(request.POST, instance=db_config)
        if form.is_valid():
            form.save()
            singleton.refresh()
            messages.success(request, 'Configuración global actualizada.')
            return redirect('global_config')
    else:
        form = GlobalConfigForm(instance=db_config)

    return render(request, 'web/global_config.html', {
        'form':      form,
        'singleton': singleton,
    })

# ── COMPOSITE: Sub-event management ──────────────────────────────────────────

@login_required
def agregar_subevento(request, pk):
    """GET: show form to add a sub-event. POST: create and attach sub-event."""
    evento_padre = get_object_or_404(Evento, pk=pk)

    if request.method == 'POST':
        form = SubEventoForm(request.POST)
        if form.is_valid():
            # Validate no circular reference
            subevento = form.save(commit=False)
            subevento.organizador = request.user
            subevento.evento_padre = evento_padre
            subevento.es_compuesto = False
            subevento.save()
            form.save_m2m()

            # Mark parent as composite
            if not evento_padre.es_compuesto:
                evento_padre.es_compuesto = True
                evento_padre.save(update_fields=['es_compuesto'])

            messages.success(
                request,
                f'✅ Sub-evento "{subevento.nombre}" añadido a "{evento_padre.nombre}".'
            )
            return redirect('event_detail', pk=pk)
    else:
        form = SubEventoForm(initial={
            'fecha_inicio': evento_padre.fecha_inicio,
            'fecha_fin': evento_padre.fecha_fin,
        })

    return render(request, 'web/subeventos.html', {
        'form': form,
        'evento_padre': evento_padre,
    })


@login_required
def eliminar_subevento(request, evento_id, subevento_id):
    """POST: remove a sub-event from its parent."""
    evento_padre = get_object_or_404(Evento, pk=evento_id)
    subevento = get_object_or_404(Evento, pk=subevento_id, evento_padre=evento_padre)

    if request.method == 'POST':
        nombre = subevento.nombre
        subevento.delete()
        # Update parent composite flag if no more sub-events
        if not evento_padre.subeventos.exists():
            evento_padre.es_compuesto = False
            evento_padre.save(update_fields=['es_compuesto'])
        messages.success(request, f'Sub-evento "{nombre}" eliminado.')
    return redirect('event_detail', pk=evento_id)


@login_required
def editar_subevento(request, evento_id, subevento_id):
    """GET/POST: edit an individual sub-event."""
    evento_padre = get_object_or_404(Evento, pk=evento_id)
    subevento    = get_object_or_404(Evento, pk=subevento_id, evento_padre=evento_padre)
    config_obj, _ = ConfiguracionEvento.objects.get_or_create(evento=subevento)

    if request.method == 'POST':
        form        = SubEventoForm(request.POST, instance=subevento)
        config_form = ConfiguracionEventoForm(request.POST, instance=config_obj)
        if form.is_valid() and config_form.is_valid():
            form.save()
            config_form.save()
            messages.success(request, f'Sub-evento "{subevento.nombre}" actualizado.')
            return redirect('event_detail', pk=evento_padre.pk)
    else:
        form        = SubEventoForm(instance=subevento)
        config_form = ConfiguracionEventoForm(instance=config_obj)

    return render(request, 'web/edit_subevento.html', {
        'form':        form,
        'config_form': config_form,
        'evento':      evento_padre,
        'subevento':   subevento,
    })


# ── BRIDGE: Report generation ─────────────────────────────────────────────────

@login_required
def generar_reporte(request, pk, tipo, formato):
    """
    Generate a report for an event using the Bridge pattern.
    tipo: 'resumen' | 'detallado' | 'financiero'
    formato: 'pdf' | 'csv' | 'html' | 'email'
    For 'pdf' formato, generates a real PDF using reportlab via ReporteCompleto.
    """
    evento = get_object_or_404(
        Evento.objects.select_related('tipo', 'ubicacion', 'organizador')
                      .prefetch_related('servicios', 'subeventos__configuracion',
                                        'subeventos__tipo', 'subeventos__ubicacion'),
        pk=pk,
    )

    if formato == 'pdf':
        # Use ReporteCompleto with real reportlab PDF generation.
        # Falls back to a downloadable HTML report if reportlab is not installed.
        reporte = ReporteCompleto()
        resultado = reporte.generar_pdf(evento)
        # HTML fallback: starts with the HTML doctype declaration
        if resultado.startswith(b'<!DOCTYPE'):
            response = HttpResponse(resultado, content_type='text/html; charset=utf-8')
            response['Content-Disposition'] = (
                f'inline; filename="reporte_completo_{evento.pk}.html"'
            )
        else:
            response = HttpResponse(resultado, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="reporte_completo_{evento.pk}.pdf"'
            )
        return response

    # Other formats use the original Bridge abstraction
    evento_dto = EventoReporte.desde_modelo(evento)
    formato_map = {
        'csv':   FormatoCSV(),
        'html':  FormatoHTML(),
        'email': FormatoEmail(),
    }
    reporte_map = {
        'resumen':    ReporteResumen,
        'detallado':  ReporteDetallado,
        'financiero': ReporteFinanciero,
    }

    fmt_obj = formato_map.get(formato, FormatoHTML())
    reporte_cls = reporte_map.get(tipo, ReporteResumen)
    reporte = reporte_cls(fmt_obj)
    contenido = reporte.generar(evento_dto)

    if formato == 'csv':
        response = HttpResponse(contenido, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = (
            f'attachment; filename="reporte_{tipo}_{evento.pk}.csv"'
        )
        return response
    elif formato == 'html':
        return render(request, 'web/reportes.html', {
            'evento': evento,
            'contenido_html': contenido,
            'tipo': tipo,
            'formato': formato,
        })
    else:  # email
        return render(request, 'web/reportes.html', {
            'evento': evento,
            'contenido_email': contenido,
            'tipo': tipo,
            'formato': formato,
        })


# ── ADAPTER: External service providers ──────────────────────────────────────

@login_required
def listar_proveedores(request, evento_id):
    """Show available service providers and contracted services for an event."""
    evento = get_object_or_404(Evento, pk=evento_id)
    proveedores = ProveedorServicio.objects.filter(activo=True)
    contratos = ServicioContratado.objects.filter(evento=evento).select_related('proveedor')

    return render(request, 'web/proveedores.html', {
        'evento': evento,
        'proveedores': proveedores,
        'contratos': contratos,
    })


@login_required
def contratar_servicio(request, evento_id, proveedor_id):
    """POST: contract a service from a provider using the Adapter pattern."""
    evento = get_object_or_404(Evento, pk=evento_id)
    proveedor = get_object_or_404(ProveedorServicio, pk=proveedor_id, activo=True)

    if request.method == 'POST':
        # Build adapter using simulated/demo credentials - no real API calls
        key = proveedor.api_key or 'simulated_key'
        adapter_factories = {
            'catering_a':  lambda: AdaptadorCateringProveedorA(),
            'catering_b':  lambda: AdaptadorCateringProveedorB(api_key=key),
            'stripe':      lambda: AdaptadorStripe(api_key=key),
            'paypal':      lambda: AdaptadorPayPal(),
            'mercadopago': lambda: AdaptadorMercadoPago(),
            'youtube':     lambda: AdaptadorYouTube(api_key=key),
            'vimeo':       lambda: AdaptadorVimeo(),
            'facebook':    lambda: AdaptadorFacebookLive(),
        }
        respuesta = {}
        factory = adapter_factories.get(proveedor.tipo)
        if factory:
            try:
                adapter = factory()
                adapter.conectar()
                respuesta = adapter.procesar_solicitud({
                    'evento_id': str(evento.pk),
                    'evento_nombre': evento.nombre,
                    'asistentes': evento.max_asistentes,
                })
            except Exception as exc:
                respuesta = {'exito': False, 'mensaje': str(exc)}

        estado = 'confirmado' if respuesta.get('exito', True) else 'pendiente'
        contrato, created = ServicioContratado.objects.get_or_create(
            evento=evento,
            proveedor=proveedor,
            defaults={
                'estado': estado,
                'respuesta_adapter': respuesta,
                'notas': respuesta.get('mensaje', ''),
            },
        )
        if not created:
            contrato.estado = estado
            contrato.respuesta_adapter = respuesta
            contrato.save(update_fields=['estado', 'respuesta_adapter'])

        messages.success(
            request,
            f'✅ Servicio "{proveedor.nombre}" contratado para "{evento.nombre}" [{estado}].'
        )

    return redirect('listar_proveedores', evento_id=evento_id)


# ── CHAIN OF RESPONSIBILITY: Event validation view ────────────────────────────

@login_required
def validar_evento(request, pk):
    """Show a detailed validation report for an event using Chain of Responsibility."""
    evento = get_object_or_404(
        Evento.objects.select_related('ubicacion').prefetch_related('configuracion'),
        pk=pk,
    )
    singleton = ConfiguracionGlobal()
    cfg = getattr(evento, 'configuracion', None)

    servicios_req = []
    if cfg:
        for campo in ('tiene_catering', 'tiene_escenario', 'tiene_iluminacion',
                      'tiene_seguridad', 'tiene_streaming', 'tiene_decoracion'):
            if getattr(cfg, campo, False):
                servicios_req.append(campo.replace('tiene_', ''))

    existentes = []
    if evento.ubicacion:
        qs = (
            Evento.objects
            .filter(ubicacion=evento.ubicacion)
            .exclude(pk=pk)
            .exclude(evento_padre=evento)   # exclude own sub-events
        )
        for ev in qs:
            existentes.append({'id': ev.pk, 'nombre': ev.nombre, 'inicio': ev.fecha_inicio, 'fin': ev.fecha_fin})

    datos = DatosValidacion(
        nombre=evento.nombre,
        max_asistentes=evento.max_asistentes,
        capacidad_ubicacion=evento.ubicacion.capacidad if evento.ubicacion else 0,
        servicios_requeridos=servicios_req,
        servicios_disponibles=['catering', 'escenario', 'iluminacion', 'seguridad', 'streaming', 'decoracion'],
        presupuesto_disponible=float(evento.presupuesto) if evento.presupuesto else 0,
        costo_estimado=0,
        fecha_inicio=evento.fecha_inicio,
        fecha_fin=evento.fecha_fin,
        eventos_existentes=existentes,
        limite_global_asistentes=singleton.get_limite_asistentes(),
        modo_mantenimiento=singleton.get_modo_mantenimiento(),
        exclude_evento_id=pk,
        costo_catering=float(evento.catering_contratado.precio) if evento.catering_contratado else 0.0,
        costo_streaming=float(evento.streaming_contratado.precio) if evento.streaming_contratado else 0.0,
    )

    # Run each validator individually for detailed UI feedback
    from .patterns.chain_of_responsibility import (
        ValidadorCapacidad, ValidadorServicios,
        ValidadorServiciosExternos, ValidadorPresupuesto,
        ValidadorHorarios, ValidadorRestriccionesGlobales,
        ResultadoValidacion,
    )

    validadores = [
        ValidadorCapacidad(),
        ValidadorServicios(),
        ValidadorServiciosExternos(),
        ValidadorPresupuesto(),
        ValidadorHorarios(),
        ValidadorRestriccionesGlobales(),
    ]

    # Sub-events are exempt from the validation chain
    if evento.evento_padre is not None:
        resultado_global = ResultadoValidacion(aprobado=True, mensaje="Sub-evento exento de validación global.")
        resultados_detalle = [
            {'nombre': v.nombre, 'aprobado': True, 'mensaje': 'Sub-evento exento'}
            for v in validadores
        ]
        return render(request, 'web/validacion_evento.html', {
            'evento': evento,
            'resultado_global': resultado_global,
            'resultados_detalle': resultados_detalle,
        })

    resultados_detalle = []
    for v in validadores:
        res = v.manejar(datos)
        resultados_detalle.append({
            'nombre': v.nombre,
            'aprobado': res.aprobado or res.validador != v.nombre,
            'mensaje': res.mensaje if res.validador == v.nombre else '',
        })

    resultado_global = construir_cadena_completa().manejar(datos)

    return render(request, 'web/validacion_evento.html', {
        'evento': evento,
        'resultado_global': resultado_global,
        'resultados_detalle': resultados_detalle,
    })


# ── CATERING / STREAMING: Adapter Pattern ─────────────────────────────────────

@login_required
def contratar_catering(request, evento_id, catering_id):
    """Contract a catering provider for an event (Adapter Pattern)."""
    from decimal import Decimal
    evento = get_object_or_404(Evento, pk=evento_id, organizador=request.user)
    catering = get_object_or_404(ProveedorCatering, pk=catering_id)

    # Budget validation: catering + streaming must not exceed event budget
    costo_streaming = evento.streaming_contratado.precio if evento.streaming_contratado else Decimal('0')
    if (catering.precio + costo_streaming) > (evento.presupuesto or Decimal('0')):
        messages.error(
            request,
            f'❌ No se puede contratar "{catering.nombre}" (€{catering.precio:,.0f}): '
            f'el coste total de servicios externos superaría el presupuesto del evento '
            f'(€{evento.presupuesto:,.0f}).'
        )
        return redirect('event_detail', pk=evento_id)

    evento.catering_contratado = catering
    evento.save(update_fields=['catering_contratado'])
    messages.success(request, f'✅ Catering "{catering.nombre}" contratado correctamente.')
    return redirect('event_detail', pk=evento_id)


@login_required
def contratar_streaming(request, evento_id, streaming_id):
    """Contract a streaming provider for an event (Adapter Pattern)."""
    from decimal import Decimal
    evento = get_object_or_404(Evento, pk=evento_id, organizador=request.user)
    streaming = get_object_or_404(ProveedorStreaming, pk=streaming_id)

    # Budget validation: catering + streaming must not exceed event budget
    costo_catering = evento.catering_contratado.precio if evento.catering_contratado else Decimal('0')
    if (costo_catering + streaming.precio) > (evento.presupuesto or Decimal('0')):
        messages.error(
            request,
            f'❌ No se puede contratar "{streaming.nombre}" (€{streaming.precio:,.0f}): '
            f'el coste total de servicios externos superaría el presupuesto del evento '
            f'(€{evento.presupuesto:,.0f}).'
        )
        return redirect('event_detail', pk=evento_id)

    evento.streaming_contratado = streaming
    evento.save(update_fields=['streaming_contratado'])
    messages.success(request, f'✅ Streaming "{streaming.nombre}" contratado correctamente.')
    return redirect('event_detail', pk=evento_id)


# ── PAYMENT GATEWAY: Adapter Pattern ─────────────────────────────────────────

@login_required
def procesar_pago(request, evento_id):
    """Display payment form and process payment using the Adapter pattern."""
    evento = get_object_or_404(Evento, pk=evento_id, organizador=request.user)

    # Only one payment per event
    if evento.pagado:
        messages.warning(request, '⚠️ Este evento ya ha sido pagado.')
        return redirect('event_detail', pk=evento_id)

    pasarelas = Pasarela.objects.filter(activa=True)
    monto_total = evento.calcular_monto_total()

    if request.method == 'POST':
        pasarela_id = request.POST.get('pasarela_id')
        if not pasarela_id:
            messages.error(request, '❌ Debes seleccionar una pasarela de pago.')
            return render(request, 'web/procesar_pago.html', {
                'evento': evento,
                'pasarelas': pasarelas,
                'monto_total': monto_total,
            })

        pasarela = get_object_or_404(Pasarela, pk=pasarela_id, activa=True)

        # Use Adapter Pattern to process the payment
        adapter = get_adapter_for_pasarela(pasarela.tipo)
        datos_evento = {
            'evento_id': str(evento.pk),
            'evento_nombre': evento.nombre,
            'asistentes': evento.max_asistentes,
        }
        resultado = adapter.procesar(monto_total, datos_evento)

        estado = 'procesada' if resultado.get('exitoso', False) else 'fallida'

        transaccion = Transaccion.objects.create(
            evento=evento,
            pasarela=pasarela,
            monto=monto_total,
            estado=estado,
            referencia_externa=resultado.get('referencia', ''),
            usuario=request.user,
        )

        if estado == 'procesada':
            from django.utils import timezone
            evento.pagado = True
            evento.fecha_pago = timezone.now()
            evento.monto_pagado = monto_total
            evento.save(update_fields=['pagado', 'fecha_pago', 'monto_pagado'])
            messages.success(
                request,
                f'✅ {resultado.get("mensaje", "Pago procesado")} — Referencia: {transaccion.referencia_externa}'
            )
        else:
            messages.error(request, '❌ El pago no pudo procesarse. Intenta de nuevo.')

        return redirect('event_detail', pk=evento_id)

    return render(request, 'web/procesar_pago.html', {
        'evento': evento,
        'pasarelas': pasarelas,
        'monto_total': monto_total,
    })


@login_required
def historial_transacciones(request):
    """Show the payment transaction history for the authenticated user."""
    transacciones = Transaccion.objects.filter(
        usuario=request.user
    ).select_related('evento', 'pasarela').order_by('-fecha')

    # Filters
    estado_filtro = request.GET.get('estado', '')
    evento_filtro = request.GET.get('evento', '')

    if estado_filtro:
        transacciones = transacciones.filter(estado=estado_filtro)
    if evento_filtro:
        transacciones = transacciones.filter(evento__nombre__icontains=evento_filtro)

    return render(request, 'web/historial_transacciones.html', {
        'transacciones': transacciones,
        'estado_filtro': estado_filtro,
        'evento_filtro': evento_filtro,
    })


@login_required
def detalle_transaccion(request, transaccion_id):
    """Show details of a single transaction."""
    transaccion = get_object_or_404(Transaccion, pk=transaccion_id, usuario=request.user)
    return render(request, 'web/detalle_transaccion.html', {
        'transaccion': transaccion,
    })


# ── BRIDGE: JSON API for events ───────────────────────────────────────────────

@login_required
def evento_api_json(request, pk):
    """Returns an event in JSON format using the Bridge pattern (ReporteEventoJSON)."""
    evento = get_object_or_404(
        Evento.objects
              .select_related('tipo', 'ubicacion', 'organizador',
                              'catering_contratado', 'streaming_contratado')
              .prefetch_related('subeventos', 'configuracion'),
        pk=pk,
    )

    if evento.organizador != request.user and not request.user.is_staff:
        return JsonResponse({"error": "No tienes permiso"}, status=403)

    reporte = ReporteEventoJSON()
    json_data = reporte.generar_json(evento)

    return JsonResponse(json.loads(json_data), safe=False)
