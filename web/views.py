from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import json

from .models import Evento, TipoEvento, ConfiguracionEvento, GlobalConfig, Ubicacion
from .forms import (
    EventoForm, ConfiguracionEventoForm, GlobalConfigForm,
    BuildEventoForm, CloneEventoForm,
)
from .patterns.singleton import ConfiguracionGlobal
from .patterns.builder import (
    EventoConferenciaBuilder, EventoBodaBuilder,
    EventoConcertBuilder, EventoTheatreBuilder, DirectorEvento,
)
from .patterns.prototype import EventoPrototype


def is_staff(user):
    return user.is_staff


# ── Dashboard ────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    eventos = Evento.objects.select_related('tipo', 'ubicacion', 'organizador')
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
    evento = get_object_or_404(
        Evento.objects
              .select_related('tipo', 'ubicacion', 'organizador')
              .prefetch_related('servicios', 'clones'),
        pk=pk,
    )
    config = ConfiguracionGlobal()
    return render(request, 'web/event_detail.html', {
        'evento': evento,
        'config': config,
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
            form.save()
            config_form.save()
            messages.success(request, f'Event "{evento.nombre}" updated successfully.')
            return redirect('event_detail', pk=evento.pk)
    else:
        form        = EventoForm(instance=evento)
        config_form = ConfiguracionEventoForm(instance=config_obj)
    return render(request, 'web/event_form.html', {
        'form':        form,
        'config_form': config_form,
        'title':       'Edit Event',
        'evento':      evento,
    })


# ── Delete ───────────────────────────────────────────────────────────────────
@login_required
def event_delete(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        nombre = evento.nombre
        evento.delete()
        messages.success(request, f'Event "{nombre}" deleted.')
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
                    f'Event cloned successfully as "{nuevo_evento.nombre}".'
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

            evento = Evento.objects.create(
                nombre         = evento_data.nombre,
                tipo           = tipo_obj,
                ubicacion      = ubicacion_obj,
                fecha_inicio   = data['fecha_inicio'],
                fecha_fin      = data['fecha_fin'],
                descripcion    = evento_data.descripcion,
                max_asistentes = evento_data.max_asistentes,
                organizador    = request.user,
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
            messages.success(request, f'Event "{evento.nombre}" built successfully.')
            return redirect('event_detail', pk=evento.pk)
    else:
        form = BuildEventoForm()

    return render(request, 'web/build_event.html', {
        'form':          form,
        'all_events':    all_events,
        'events_json':   json.dumps(events_json),
        'services_list': [
            ('Catering',   '🍽️', 'catering'),
            ('Stage',      '🎭', 'escenario'),
            ('Lighting',   '💡', 'iluminacion'),
            ('Security',   '🔒', 'seguridad'),
            ('Streaming',  '📡', 'streaming'),
            ('Decoration', '🎨', 'decoracion'),
        ],
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
            messages.success(
                request,
                f'Event cloned successfully as "{nuevo_evento.nombre}".'
            )
            return redirect('event_detail', pk=nuevo_evento.pk)
    else:
        form = CloneEventoForm(initial={
            'nombre':        f"Copy of {original.nombre}",
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
            messages.success(request, 'Global configuration updated.')
            return redirect('global_config')
    else:
        form = GlobalConfigForm(instance=db_config)

    return render(request, 'web/global_config.html', {
        'form':      form,
        'singleton': singleton,
    })