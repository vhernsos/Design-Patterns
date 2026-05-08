from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import json

from .models import Evento, TipoEvento, ConfiguracionEvento, GlobalConfig, Ubicacion, ProveedorServicio, ServicioContratado, Pasarela, Transaccion, ProveedorCatering, ProveedorStreaming, HistorialNotificacion
from .forms import (
    EventoForm, ConfiguracionEventoForm, GlobalConfigForm,
    BuildEventoForm, CloneEventoForm, EventoUpdateForm, SubEventoForm,
)
from .patterns.singleton import ConfiguracionGlobal
from .patterns.builder import (
    EventoConferenciaBuilder, EventoBodaBuilder,
    EventoConcertBuilder, EventoTheatreBuilder, DirectorEvento,
)
from .patterns.prototype import EventoPrototype, PrototypeEventos
from .patterns.chain_of_responsibility import (
    DatosValidacion, construir_cadena_completa,
)
from .patterns.bridge import (
    crear_reporte,
)
from .patterns.adapter import (
    AdaptadorCateringProveedorA, AdaptadorCateringProveedorB,
    AdaptadorStripe, AdaptadorPayPal, AdaptadorMercadoPago,
    AdaptadorYouTube, AdaptadorVimeo, AdaptadorFacebookLive,
    get_adapter_for_pasarela,
)
from .patterns.decorator import (
    aplicar_decoradores, DECORADORES_DISPONIBLES, DECORADORES_LABELS,
)
from .patterns.calculator import CalculadoraCostes
from .patterns.observer import construir_observable_con_observadores
from .patterns.template_method import crear_proceso_evento


def is_staff(user):
    return user.is_staff


                                                                                

def _construir_datos_validacion(evento_form_data, ubicacion_obj=None, config=None,
                                exclude_evento_id=None) -> DatosValidacion:
    singleton = ConfiguracionGlobal()
    servicios_req = []
    cfg = evento_form_data
    for campo in ('tiene_catering', 'tiene_escenario', 'tiene_iluminacion',
                  'tiene_seguridad', 'tiene_streaming', 'tiene_decoracion'):
        if cfg.get(campo):
            servicios_req.append(campo.replace('tiene_', ''))

    capacidad_ub = ubicacion_obj.capacidad if ubicacion_obj else 0

                                                                                
                                                                                
                                                                          
    existentes = []
    if ubicacion_obj:
        qs = Evento.objects.filter(ubicacion=ubicacion_obj, evento_padre__isnull=True)
        for ev in qs:
            existentes.append({'id': ev.pk, 'nombre': ev.nombre, 'inicio': ev.fecha_inicio, 'fin': ev.fecha_fin})

                                                          
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
        catering_contratado=catering_obj,
        streaming_contratado=streaming_obj,
        decoradores=cfg.get('decoradores') or [],
    )


                                                                               
@login_required
def dashboard(request):
                                                                                      
    eventos = Evento.objects.select_related('tipo', 'ubicacion', 'organizador').filter(
        evento_padre__isnull=True
    )
    tipo_id = request.GET.get('tipo')
    fecha   = request.GET.get('fecha')
    if tipo_id:
        eventos = eventos.filter(tipo__nombre__iexact=tipo_id)
    if fecha:
        eventos = eventos.filter(fecha_inicio__date=fecha)

    config = ConfiguracionGlobal()
    tipos  = TipoEvento.objects.all()
    tipos_eventos = ['boda', 'concierto', 'teatro', 'conferencia']
    return render(request, 'web/dashboard.html', {
        'eventos': eventos,
        'tipos':   tipos,
        'config':  config,
        'cantidad_tipos': len(tipos_eventos),
    })


                                                                               
@login_required
def event_detail(request, pk):
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

    costos = CalculadoraCostes.calcular_costo_total(evento)
    monto_total = costos['costos_totales']

                                                                                
    decoradores_activos = evento.decoradores or []
    evento_decorado = aplicar_decoradores(evento, decoradores_activos)
    precio_decorado = evento_decorado.obtener_precio()
    descripcion_decorada = evento_decorado.obtener_descripcion()
    costo_decoradores = costos['costo_decorator_total']

                                                                    
    decoradores_info = [
        {
            'key': key,
            'nombre': DECORADORES_LABELS[key][0],
            'precio': DECORADORES_LABELS[key][1],
            'activo': key in decoradores_activos,
        }
        for key in DECORADORES_DISPONIBLES
    ]

    return render(request, 'web/event_detail.html', {
        'evento': evento,
        'config': config,
        'catererings': catererings,
        'streamings': streamings,
        'pasarelas': pasarelas,
        'monto_total': monto_total,
        'costos': costos,
                   
        'decoradores_info': decoradores_info,
        'precio_decorado': precio_decorado,
        'descripcion_decorada': descripcion_decorada,
        'costo_decoradores': costo_decoradores,
        'decoradores_activos': decoradores_activos,
    })


                                                                               
@login_required
def event_update(request, pk):
    evento = get_object_or_404(
        Evento.objects.select_related('catering_contratado', 'streaming_contratado'),
        pk=pk,
        organizador=request.user,
    )
    if evento.evento_padre_id:
        return redirect(
            'editar_subevento',
            evento_id=evento.evento_padre_id,
            subevento_id=evento.pk,
        )

    if request.method == 'POST':
        presupuesto_anterior = evento.presupuesto
        catering_anterior = evento.catering_contratado
        streaming_anterior = evento.streaming_contratado

        form = EventoUpdateForm(request.POST, instance=evento)
        if form.is_valid():
            if evento.evento_padre is not None:
                form.save()
                messages.success(request, f'Sub-evento "{evento.nombre}" actualizado exitosamente.')
                return redirect('event_detail', pk=evento.pk)

            datos_validacion = _construir_datos_validacion(form.cleaned_data, exclude_evento_id=evento.pk)
            resultado = construir_cadena_completa().manejar(datos_validacion)
            if not resultado.aprobado:
                messages.error(
                    request,
                    f'❌ Validación fallida [{resultado.validador}]: {resultado.mensaje}',
                )
            else:
                evento = form.save()
                observable = construir_observable_con_observadores(evento)
                cambios_notificados = 0

                if presupuesto_anterior != evento.presupuesto:
                    observable.notificar(
                        'evento_presupuesto_cambió',
                        {
                            'presupuesto_anterior': float(presupuesto_anterior or 0),
                            'presupuesto_nuevo': float(evento.presupuesto or 0),
                            'diferencia': float((evento.presupuesto or 0) - (presupuesto_anterior or 0)),
                        }
                    )
                    HistorialNotificacion.objects.create(
                        evento=evento,
                        tipo='evento_actualizado',
                        mensaje='Presupuesto actualizado',
                        detalles={
                            'presupuesto_anterior': str(presupuesto_anterior or 0),
                            'presupuesto_nuevo': str(evento.presupuesto or 0),
                        },
                        enviado_a='Email, Proveedor, Analítica',
                    )
                    cambios_notificados += 1

                if catering_anterior != evento.catering_contratado:
                    if catering_anterior:
                        observable.remover_servicio_adapter('catering', catering_anterior.nombre)
                        HistorialNotificacion.objects.create(
                            evento=evento,
                            tipo='evento_actualizado',
                            mensaje=f'Catering removido: {catering_anterior.nombre}',
                            detalles={'tipo': 'catering', 'nombre': catering_anterior.nombre},
                            enviado_a='Email, Proveedor, Analítica',
                        )
                        cambios_notificados += 1
                    if evento.catering_contratado:
                        observable.agregar_servicio_adapter(
                            'catering',
                            evento.catering_contratado.nombre,
                            float(evento.catering_contratado.precio),
                        )
                        HistorialNotificacion.objects.create(
                            evento=evento,
                            tipo='evento_actualizado',
                            mensaje=f'Catering agregado: {evento.catering_contratado.nombre}',
                            detalles={
                                'tipo': 'catering',
                                'nombre': evento.catering_contratado.nombre,
                                'precio': str(evento.catering_contratado.precio),
                            },
                            enviado_a='Email, Proveedor, Analítica',
                        )
                        cambios_notificados += 1

                if streaming_anterior != evento.streaming_contratado:
                    if streaming_anterior:
                        observable.remover_servicio_adapter('streaming', streaming_anterior.nombre)
                        HistorialNotificacion.objects.create(
                            evento=evento,
                            tipo='evento_actualizado',
                            mensaje=f'Streaming removido: {streaming_anterior.nombre}',
                            detalles={'tipo': 'streaming', 'nombre': streaming_anterior.nombre},
                            enviado_a='Email, Proveedor, Analítica',
                        )
                        cambios_notificados += 1
                    if evento.streaming_contratado:
                        observable.agregar_servicio_adapter(
                            'streaming',
                            evento.streaming_contratado.nombre,
                            float(evento.streaming_contratado.precio),
                        )
                        HistorialNotificacion.objects.create(
                            evento=evento,
                            tipo='evento_actualizado',
                            mensaje=f'Streaming agregado: {evento.streaming_contratado.nombre}',
                            detalles={
                                'tipo': 'streaming',
                                'nombre': evento.streaming_contratado.nombre,
                                'precio': str(evento.streaming_contratado.precio),
                            },
                            enviado_a='Email, Proveedor, Analítica',
                        )
                        cambios_notificados += 1

                if cambios_notificados == 0:
                    HistorialNotificacion.objects.create(
                        evento=evento,
                        tipo='evento_actualizado',
                        mensaje='Evento actualizado sin cambios de presupuesto ni servicios',
                        detalles={},
                        enviado_a='Email, Proveedor, Analítica',
                    )
                messages.success(request, f'Evento "{evento.nombre}" actualizado exitosamente.')
                return redirect('event_detail', pk=evento.pk)
    else:
        form = EventoUpdateForm(instance=evento)
    return render(request, 'web/event_update.html', {
        'form': form,
        'evento': evento,
    })


                                                                               
@login_required
def event_delete(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        nombre = evento.nombre
        evento.delete()
        messages.success(request, f'Evento "{nombre}" eliminado.')
        return redirect('dashboard')
    return render(request, 'web/event_confirm_delete.html', {'evento': evento})


                                                                               
@login_required
def build_event(request):
    all_events = Evento.objects.select_related(
        'tipo', 'ubicacion'
    ).prefetch_related('configuracion').filter(
        organizador=request.user,
        evento_padre__isnull=True,
        es_clon=False,
    ).order_by('-creado_en')

                                                                  
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
            'presupuesto':  str(ev.presupuesto or 0),
            'config':       cfg,
        })

    if request.method == 'POST':
        form = BuildEventoForm(request.POST)
        if form.is_valid():
            data       = form.cleaned_data
            build_mode = data['build_mode']

                                                                               
            if build_mode == 'from_clone':
                original = get_object_or_404(
                    Evento,
                    pk=data['source_event_id'],
                    organizador=request.user,
                )
                try:
                    nuevo_evento = PrototypeEventos.clonar_evento(
                        original,
                        request.user,
                        nombre=data['nombre'],
                        fecha_inicio=data['fecha_inicio'],
                        fecha_fin=data['fecha_fin'],
                        max_asistentes=data['max_asistentes'],
                        descripcion=data.get('descripcion', ''),
                        presupuesto=data.get('presupuesto') if data.get('presupuesto') is not None else original.presupuesto,
                    )
                except ValueError as exc:
                    messages.error(request, str(exc))
                    return redirect('build_event')

                if hasattr(nuevo_evento, 'configuracion'):
                    nuevo_evento.configuracion.tiene_catering = data.get('tiene_catering', False)
                    nuevo_evento.configuracion.tiene_escenario = data.get('tiene_escenario', False)
                    nuevo_evento.configuracion.tiene_iluminacion = data.get('tiene_iluminacion', False)
                    nuevo_evento.configuracion.tiene_seguridad = data.get('tiene_seguridad', False)
                    nuevo_evento.configuracion.tiene_streaming = data.get('tiene_streaming', False)
                    nuevo_evento.configuracion.tiene_decoracion = data.get('tiene_decoracion', False)
                    nuevo_evento.configuracion.save()

                messages.success(
                    request,
                    f'Evento clonado exitosamente como "{nuevo_evento.nombre}".'
                )
                return redirect('event_detail', pk=nuevo_evento.pk)

                                                                               
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

            else:          
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

                                                                               
            tipo_obj, _ = TipoEvento.objects.get_or_create(nombre=evento_data.tipo)
            ubicacion_obj = None
            if evento_data.ubicacion:
                ubicacion_obj, _ = Ubicacion.objects.get_or_create(
                    nombre=evento_data.ubicacion,
                    defaults={'direccion': '', 'ciudad': ''},
                )

                                                                                
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
                presupuesto           = data.get('presupuesto') or 0,
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

                                                                            
            import re as _re
            from django.utils.dateparse import parse_datetime as _parse_dt
                                                                       
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
                sub_fi = _parse_dt(sub_fecha_inicio) or data['fecha_inicio']
                sub_ff = _parse_dt(sub_fecha_fin)    or data['fecha_fin']

                sub_tipo_obj = tipo_obj
                if sub_tipo_nombre:
                    sub_tipo_obj, _ = TipoEvento.objects.get_or_create(nombre=sub_tipo_nombre)

                                                          
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
                subevento = Evento.objects.create(
                    nombre         = sub_nombre,
                    tipo           = sub_tipo_obj,
                    ubicacion      = sub_ubicacion_obj,
                    fecha_inicio   = sub_fi,
                    fecha_fin      = sub_ff,
                    max_asistentes = sub_max_int,
                    organizador    = request.user,
                    evento_padre   = evento,
                    es_compuesto   = False,
                )
                                    
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


                                                                                
@login_required
def clone_event(request, pk):
    original = get_object_or_404(Evento, pk=pk, organizador=request.user)
    if original.evento_padre_id is not None:
        messages.error(
            request,
            "No se pueden clonar subeventos. Clona el evento principal.",
        )
        return redirect('event_detail', pk=original.pk)
    if original.es_clon:
        messages.error(
            request,
            "No se pueden clonar clones. Clona el evento original.",
        )
        return redirect('event_detail', pk=original.pk)

    if request.method == 'POST':
        form = CloneEventoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                nuevo_evento = PrototypeEventos.clonar_evento(
                    original,
                    request.user,
                    nombre=data['nombre'],
                    fecha_inicio=data['fecha_inicio'],
                    fecha_fin=data['fecha_fin'],
                    max_asistentes=data['max_asistentes'],
                    descripcion=data.get('descripcion', ''),
                )
            except ValueError as exc:
                messages.error(request, str(exc))
                return redirect('event_detail', pk=original.pk)

            messages.success(request, f'Evento clonado exitosamente como "{nuevo_evento.nombre}".')
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

                                                                               

@login_required
def agregar_subevento(request, pk):
    evento_padre = get_object_or_404(Evento, pk=pk)

    if request.method == 'POST':
        form = SubEventoForm(request.POST)
        if form.is_valid():
                                            
            subevento = form.save(commit=False)
            subevento.organizador = request.user
            subevento.evento_padre = evento_padre
            subevento.es_compuesto = False
            subevento.save()
            form.save_m2m()

                                      
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
    evento_padre = get_object_or_404(Evento, pk=evento_id)
    subevento = get_object_or_404(Evento, pk=subevento_id, evento_padre=evento_padre)

    if request.method == 'POST':
        nombre = subevento.nombre
        subevento.delete()
                                                            
        if not evento_padre.subeventos.exists():
            evento_padre.es_compuesto = False
            evento_padre.save(update_fields=['es_compuesto'])
        messages.success(request, f'Sub-evento "{nombre}" eliminado.')
    return redirect('event_detail', pk=evento_id)


@login_required
def editar_subevento(request, evento_id, subevento_id):
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


                                                                                

@login_required
def generar_reporte(request, pk, tipo, formato):
    evento = get_object_or_404(Evento, pk=pk)

    try:
        reporte = crear_reporte(tipo, formato)
        contenido = reporte.generar(evento)

        if formato == 'json':
            response = HttpResponse(contenido, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename=\"evento_{evento.id}.json\"'
        elif formato == 'csv':
            response = HttpResponse(contenido, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename=\"evento_{evento.id}.csv\"'
        elif formato == 'html':
            response = HttpResponse(contenido, content_type='text/html')
        elif formato == 'pdf':
            response = HttpResponse(contenido, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=\"evento_{evento.id}.pdf\"'
        elif formato == 'email':
            response = HttpResponse(contenido, content_type='text/plain')
        else:
            raise ValueError(f'Formato no soportado: {formato}')

        return response
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('event_detail', pk=evento.pk)


@login_required
def descargar_reporte(request, pk):
    tipo_reporte = request.GET.get('tipo', 'resumen')
    formato = request.GET.get('formato', 'json')
    return generar_reporte(request, pk, tipo_reporte, formato)


                                                                               

@login_required
def listar_proveedores(request, evento_id):
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
    evento = get_object_or_404(Evento, pk=evento_id)
    proveedor = get_object_or_404(ProveedorServicio, pk=proveedor_id, activo=True)

    if request.method == 'POST':
                                                                            
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


                                                                                

@login_required
def validar_evento(request, pk):
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
            .exclude(evento_padre=evento)                           
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
        catering_contratado=evento.catering_contratado,
        streaming_contratado=evento.streaming_contratado,
        decoradores=list(evento.decoradores or []),
    )

                                                              
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


                                                                                

@login_required
def contratar_catering(request, evento_id, catering_id):
    from decimal import Decimal
    evento = get_object_or_404(Evento.objects.select_related('streaming_contratado', 'catering_contratado'), pk=evento_id, organizador=request.user)
    catering = get_object_or_404(ProveedorCatering, pk=catering_id)

    catering_anterior = evento.catering_contratado
    evento.catering_contratado = catering
    costos = CalculadoraCostes.calcular_costo_total(evento)
    costo_extras = costos['costo_adapter_total'] + costos['costo_decorator_total']
    if costo_extras > evento.obtener_presupuesto_efectivo() and evento.obtener_presupuesto_efectivo() > Decimal('0'):
        evento.catering_contratado = catering_anterior
        messages.error(
            request,
            f'❌ No se puede contratar "{catering.nombre}" (€{catering.precio:,.0f}): '
            f'el coste adicional (€{costo_extras:,.0f}) superaría el presupuesto disponible '
            f'(€{evento.obtener_presupuesto_efectivo():,.0f}).'
        )
        return redirect('event_detail', pk=evento_id)

    evento.save(update_fields=['catering_contratado'])

    observable = construir_observable_con_observadores(evento)
    if catering_anterior and catering_anterior != catering:
        observable.remover_servicio_adapter('catering', catering_anterior.nombre)
    observable.agregar_servicio_adapter('catering', catering.nombre, float(catering.precio))
    HistorialNotificacion.objects.create(
        evento=evento,
        tipo='evento_actualizado',
        mensaje=f'Catering contratado: {catering.nombre}',
        detalles={'tipo': 'catering', 'nombre': catering.nombre, 'precio': str(catering.precio)},
        enviado_a='Email, Proveedor, Analítica',
    )

    messages.success(request, f'✅ Catering "{catering.nombre}" contratado correctamente.')
    return redirect('event_detail', pk=evento_id)


@login_required
def contratar_streaming(request, evento_id, streaming_id):
    from decimal import Decimal
    evento = get_object_or_404(Evento.objects.select_related('streaming_contratado', 'catering_contratado'), pk=evento_id, organizador=request.user)
    streaming = get_object_or_404(ProveedorStreaming, pk=streaming_id)

    streaming_anterior = evento.streaming_contratado
    evento.streaming_contratado = streaming
    costos = CalculadoraCostes.calcular_costo_total(evento)
    costo_extras = costos['costo_adapter_total'] + costos['costo_decorator_total']
    if costo_extras > evento.obtener_presupuesto_efectivo() and evento.obtener_presupuesto_efectivo() > Decimal('0'):
        evento.streaming_contratado = streaming_anterior
        messages.error(
            request,
            f'❌ No se puede contratar "{streaming.nombre}" (€{streaming.precio:,.0f}): '
            f'el coste adicional (€{costo_extras:,.0f}) superaría el presupuesto disponible '
            f'(€{evento.obtener_presupuesto_efectivo():,.0f}).'
        )
        return redirect('event_detail', pk=evento_id)

    evento.save(update_fields=['streaming_contratado'])

    observable = construir_observable_con_observadores(evento)
    if streaming_anterior and streaming_anterior != streaming:
        observable.remover_servicio_adapter('streaming', streaming_anterior.nombre)
    observable.agregar_servicio_adapter('streaming', streaming.nombre, float(streaming.precio))
    HistorialNotificacion.objects.create(
        evento=evento,
        tipo='evento_actualizado',
        mensaje=f'Streaming contratado: {streaming.nombre}',
        detalles={'tipo': 'streaming', 'nombre': streaming.nombre, 'precio': str(streaming.precio)},
        enviado_a='Email, Proveedor, Analítica',
    )

    messages.success(request, f'✅ Streaming "{streaming.nombre}" contratado correctamente.')
    return redirect('event_detail', pk=evento_id)


                                                                               

@login_required
def procesar_pago(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id, organizador=request.user)

                                
    if evento.pagado:
        messages.warning(request, '⚠️ Este evento ya ha sido pagado.')
        return redirect('event_detail', pk=evento_id)

    pasarelas = Pasarela.objects.filter(activa=True)
    monto_total = CalculadoraCostes.calcular_costo_total(evento)['costos_totales']

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

                                            
            observable = construir_observable_con_observadores(evento)
            observable.registrar_pago(float(monto_total), pasarela.nombre)
            HistorialNotificacion.objects.create(
                evento=evento,
                tipo='evento_pagado',
                mensaje=f'Pago procesado: €{monto_total} via {pasarela.nombre}',
                detalles={
                    'monto': str(monto_total),
                    'pasarela': pasarela.nombre,
                    'referencia': transaccion.referencia_externa,
                },
                enviado_a='Email, Proveedor, Analítica',
            )

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
    transacciones = Transaccion.objects.filter(
        usuario=request.user
    ).select_related('evento', 'pasarela').order_by('-fecha')

             
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
    transaccion = get_object_or_404(Transaccion, pk=transaccion_id, usuario=request.user)
    return render(request, 'web/detalle_transaccion.html', {
        'transaccion': transaccion,
    })


                                                                                

@login_required
def evento_api_json(request, pk):
    evento = get_object_or_404(
        Evento.objects
              .select_related('tipo', 'ubicacion', 'organizador',
                              'catering_contratado', 'streaming_contratado')
              .prefetch_related('subeventos', 'configuracion'),
        pk=pk,
    )

    if evento.organizador != request.user and not request.user.is_staff:
        return JsonResponse({"error": "No tienes permiso"}, status=403)

    reporte = crear_reporte('completo', 'json')
    return HttpResponse(reporte.generar(evento), content_type='application/json')


                                                                                

@login_required
def toggle_decorador(request, evento_id, decorador_key):
    evento = get_object_or_404(Evento, pk=evento_id, organizador=request.user)

    if decorador_key not in DECORADORES_DISPONIBLES:
        messages.error(request, f'❌ Decorador desconocido: {decorador_key}')
        return redirect('event_detail', pk=evento_id)

    if request.method == 'POST':
        activos = list(evento.decoradores or [])
        nombre = DECORADORES_LABELS[decorador_key][0]
        precio = DECORADORES_DISPONIBLES[decorador_key].PRECIO
        observable = construir_observable_con_observadores(evento)

        if decorador_key in activos:
            activos.remove(decorador_key)
            evento.decoradores = activos
            evento.save(update_fields=['decoradores'])
            observable.remover_decorador(nombre)
            HistorialNotificacion.objects.create(
                evento=evento,
                tipo='evento_actualizado',
                mensaje=f'Extra eliminado: {nombre}',
                detalles={'nombre': nombre},
                enviado_a='Email, Proveedor, Analítica',
            )
            messages.success(request, f'✅ Extra "{nombre}" eliminado del evento.')
        else:
            activos.append(decorador_key)
            evento.decoradores = activos
            evento.save(update_fields=['decoradores'])
            observable.agregar_decorador(nombre, float(precio))
            HistorialNotificacion.objects.create(
                evento=evento,
                tipo='evento_actualizado',
                mensaje=f'Extra agregado: {nombre}',
                detalles={'nombre': nombre, 'precio': str(precio)},
                enviado_a='Email, Proveedor, Analítica',
            )
            messages.success(request, f'✅ Extra "{nombre}" (€{precio}) añadido al evento.')

    return redirect('event_detail', pk=evento_id)


                                                                               

@login_required
def confirmar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk, organizador=request.user)

    if evento.confirmado:
        messages.warning(request, '⚠️ El evento ya estaba confirmado.')
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        proceso = crear_proceso_evento(evento, evento.tipo_evento)
        exito = proceso.ejecutar_proceso()
        historial = proceso.obtener_historial()

                                              
        observable = construir_observable_con_observadores(evento)
        if exito:
            observable.cambiar_estado('confirmado')
            HistorialNotificacion.objects.create(
                evento=evento,
                tipo='evento_estado_cambió',
                mensaje=f'Evento confirmado mediante Template Method ({evento.tipo_evento})',
                detalles={'tipo_evento': evento.tipo_evento, 'pasos': len(historial)},
                enviado_a='Email, Proveedor, Analítica',
            )
            messages.success(
                request,
                f'✅ Evento confirmado correctamente usando el flujo de {evento.get_tipo_evento_display()}.'
            )
        else:
                                          
            error_msg = next(
                (p['resultado'].get('error', '') for p in historial if p['estado'] == 'error'),
                'Error desconocido'
            )
            messages.error(request, f'❌ No se pudo confirmar el evento: {error_msg}')

        return render(request, 'web/confirmar_evento.html', {
            'evento': evento,
            'exito': exito,
            'historial': historial,
        })

    return render(request, 'web/confirmar_evento.html', {
        'evento': evento,
        'exito': None,
        'historial': [],
    })


                                                                                

@login_required
def historial_notificaciones(request, pk):
    evento = get_object_or_404(Evento, pk=pk, organizador=request.user)
    notificaciones = evento.notificaciones.all()
    return render(request, 'web/historial_notificaciones.html', {
        'evento': evento,
        'notificaciones': notificaciones,
    })
