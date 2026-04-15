"""
Adapter Pattern — Adaptador
============================
Propósito:
    Integrar sistemas externos (proveedores de catering, pasarelas de pago,
    plataformas de streaming) con una interfaz uniforme, de modo que el
    código cliente no dependa de la API concreta de cada proveedor.

Estructura:
    IServicioExterno (interfaz uniforme)
        │
        ├── Catering
        │     ├── AdaptadorCateringProveedorA  → CateringProveedorA (sistema legado)
        │     └── AdaptadorCateringProveedorB  → CateringProveedorB (sistema legado)
        │
        ├── Pagos
        │     ├── AdaptadorStripe      → StripeAPI
        │     ├── AdaptadorPayPal      → PayPalAPI
        │     └── AdaptadorMercadoPago → MercadoPagoAPI
        │
        └── Streaming
              ├── AdaptadorYouTube     → YouTubeStreamAPI
              ├── AdaptadorVimeo       → VimeoStreamAPI
              └── AdaptadorFacebookLive → FacebookLiveAPI

Uso típico:
    pasarela = AdaptadorStripe(api_key="sk_test_...")
    pasarela.conectar()
    resultado = pasarela.procesar_solicitud({"monto": 500, "moneda": "USD"})
    estado    = pasarela.obtener_estado()
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any


# ---------------------------------------------------------------------------
# Interfaz uniforme para todos los servicios externos
# ---------------------------------------------------------------------------

class IServicioExterno(ABC):
    """
    Interfaz uniforme que todos los adaptadores deben implementar.
    El código cliente (views.py, etc.) solo conoce esta interfaz,
    nunca los sistemas externos directamente.
    """

    @abstractmethod
    def conectar(self) -> bool:
        """
        Establece la conexión con el proveedor externo.
        Devuelve True si la conexión fue exitosa.
        """

    @abstractmethod
    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía una solicitud al proveedor y devuelve el resultado.
        El diccionario de entrada y salida depende del tipo de servicio
        pero siempre incluye 'exito' (bool) y 'mensaje' (str).
        """

    @abstractmethod
    def obtener_estado(self) -> Dict[str, Any]:
        """
        Consulta el estado actual del servicio/proveedor.
        Devuelve un dict con al menos 'conectado' (bool) y 'proveedor' (str).
        """

    @property
    def nombre_proveedor(self) -> str:
        """Nombre legible del proveedor."""
        return self.__class__.__name__


# ===========================================================================
# SISTEMAS EXTERNOS SIMULADOS (APIs de terceros)
# Representan las interfaces incompatibles que los Adapters deben adaptar.
# ===========================================================================

# ---------------------------------------------------------------------------
# Catering — Proveedor A (API REST estilo antiguo)
# ---------------------------------------------------------------------------

class CateringProveedorA:
    """Sistema legado de catering con su propia interfaz propietaria."""

    def __init__(self, endpoint: str = "https://catering-a.example.com"):
        self.endpoint = endpoint
        self._activo = False

    def iniciar_sesion(self, usuario: str, password: str) -> bool:
        """Interfaz propia del Proveedor A para autenticarse."""
        self._activo = True
        print(f"[CateringProveedorA] Sesión iniciada en {self.endpoint}")
        return True

    def crear_pedido(self, evento_id: str, menu: str, comensales: int) -> dict:
        """Crea un pedido de catering con la interfaz propia del proveedor."""
        return {
            "pedido_id": f"PA-{evento_id}-001",
            "estado": "confirmado",
            "menu": menu,
            "comensales": comensales,
        }

    def consultar_pedido(self, pedido_id: str) -> dict:
        return {"pedido_id": pedido_id, "estado": "en_preparacion", "activo": self._activo}


class AdaptadorCateringProveedorA(IServicioExterno):
    """
    Adapta CateringProveedorA a la interfaz IServicioExterno.
    Traduce conectar/procesar_solicitud/obtener_estado a la API del proveedor.
    """

    def __init__(self, usuario: str = "admin", password: str = "secret",
                 endpoint: str = "https://catering-a.example.com"):
        self._proveedor = CateringProveedorA(endpoint)
        self._usuario   = usuario
        self._password  = password
        self._conectado = False
        self._ultimo_pedido: dict = {}

    def conectar(self) -> bool:
        self._conectado = self._proveedor.iniciar_sesion(self._usuario, self._password)
        return self._conectado

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {evento_id, menu, comensales}
        """
        if not self._conectado:
            return {"exito": False, "mensaje": "No conectado al Proveedor A"}
        pedido = self._proveedor.crear_pedido(
            evento_id=datos.get("evento_id", "EVT-000"),
            menu=datos.get("menu", "Menú estándar"),
            comensales=datos.get("comensales", 100),
        )
        self._ultimo_pedido = pedido
        return {"exito": True, "mensaje": "Pedido creado", "referencia": pedido["pedido_id"]}

    def obtener_estado(self) -> Dict[str, Any]:
        return {
            "conectado": self._conectado,
            "proveedor": "Catering Proveedor A",
            "ultimo_pedido": self._ultimo_pedido,
        }


# ---------------------------------------------------------------------------
# Catering — Proveedor B (API GraphQL estilo moderno)
# ---------------------------------------------------------------------------

class CateringProveedorB:
    """Sistema moderno de catering con API GraphQL."""

    def __init__(self, api_key: str = ""):
        self.api_key  = api_key
        self._sesion  = None

    def authenticate(self, api_key: str) -> dict:
        self._sesion = {"token": f"tok_{api_key[:8]}", "expira_en": 3600}
        print("[CateringProveedorB] Autenticado correctamente")
        return self._sesion

    def submitOrder(self, payload: dict) -> dict:   # noqa: N802
        return {
            "orderId": f"B-{payload.get('eventName', 'EVT')[:5].upper()}-099",
            "status":  "ACCEPTED",
            "estimatedDelivery": "2025-06-01T12:00:00",
        }

    def getOrderStatus(self, order_id: str) -> dict:   # noqa: N802
        return {"orderId": order_id, "status": "PROCESSING", "session": self._sesion}


class AdaptadorCateringProveedorB(IServicioExterno):
    """
    Adapta CateringProveedorB (API camelCase/GraphQL) a IServicioExterno.
    """

    def __init__(self, api_key: str = "api_key_demo"):
        self._proveedor  = CateringProveedorB(api_key)
        self._api_key    = api_key
        self._sesion     = None
        self._ultimo_id  = ""

    def conectar(self) -> bool:
        self._sesion = self._proveedor.authenticate(self._api_key)
        return self._sesion is not None

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {event_name, menu_type, guests}
        """
        if not self._sesion:
            return {"exito": False, "mensaje": "Sin sesión activa"}
        respuesta = self._proveedor.submitOrder({
            "eventName": datos.get("event_name", "Evento"),
            "menuType":  datos.get("menu_type", "standard"),
            "guests":    datos.get("guests", 100),
        })
        self._ultimo_id = respuesta["orderId"]
        return {"exito": True, "mensaje": "Orden aceptada", "referencia": self._ultimo_id}

    def obtener_estado(self) -> Dict[str, Any]:
        estado = {}
        if self._ultimo_id:
            estado = self._proveedor.getOrderStatus(self._ultimo_id)
        return {
            "conectado": self._sesion is not None,
            "proveedor": "Catering Proveedor B",
            "ultimo_pedido": estado,
        }


# ===========================================================================
# PASARELAS DE PAGO
# ===========================================================================

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

class StripeAPI:
    """Simulación de la SDK de Stripe."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def create_payment_intent(self, amount: int, currency: str) -> dict:
        print(f"[Stripe] Creando PaymentIntent — {amount} {currency.upper()}")
        return {"id": f"pi_{amount}_{currency}", "status": "requires_payment_method"}

    def confirm_payment(self, intent_id: str) -> dict:
        return {"id": intent_id, "status": "succeeded"}

    def retrieve(self, intent_id: str) -> dict:
        return {"id": intent_id, "status": "succeeded", "livemode": False}


class AdaptadorStripe(IServicioExterno):
    """Adapta StripeAPI a IServicioExterno."""

    def __init__(self, api_key: str = "sk_test_demo"):
        self._stripe    = StripeAPI(api_key)
        self._conectado = False
        self._intent_id = ""

    def conectar(self) -> bool:
        # Stripe no requiere conexión explícita; validamos la clave aquí.
        self._conectado = self._stripe.api_key.startswith("sk_")
        return self._conectado

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {monto (en centavos), moneda}
        """
        intent = self._stripe.create_payment_intent(
            amount=int(datos.get("monto", 0) * 100),
            currency=datos.get("moneda", "usd"),
        )
        confirmacion = self._stripe.confirm_payment(intent["id"])
        self._intent_id = intent["id"]
        return {
            "exito":     confirmacion["status"] == "succeeded",
            "mensaje":   f"Pago {confirmacion['status']}",
            "referencia": self._intent_id,
        }

    def obtener_estado(self) -> Dict[str, Any]:
        estado = {}
        if self._intent_id:
            estado = self._stripe.retrieve(self._intent_id)
        return {"conectado": self._conectado, "proveedor": "Stripe", "ultimo_pago": estado}


# ---------------------------------------------------------------------------
# PayPal
# ---------------------------------------------------------------------------

class PayPalAPI:
    """Simulación del API REST de PayPal."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id     = client_id
        self.client_secret = client_secret
        self._access_token = ""

    def get_access_token(self) -> str:
        self._access_token = f"A21AA{self.client_id[:6]}"
        print(f"[PayPal] Token obtenido: {self._access_token}")
        return self._access_token

    def create_order(self, amount: str, currency_code: str) -> dict:
        return {"id": f"ORD-PP-{amount}", "status": "CREATED"}

    def capture_order(self, order_id: str) -> dict:
        return {"id": order_id, "status": "COMPLETED"}


class AdaptadorPayPal(IServicioExterno):
    """Adapta PayPalAPI a IServicioExterno."""

    def __init__(self, client_id: str = "CLIENT_DEMO", client_secret: str = "SECRET_DEMO"):
        self._paypal    = PayPalAPI(client_id, client_secret)
        self._conectado = False
        self._order_id  = ""

    def conectar(self) -> bool:
        token           = self._paypal.get_access_token()
        self._conectado = bool(token)
        return self._conectado

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {monto, moneda}
        """
        orden = self._paypal.create_order(
            amount=str(datos.get("monto", 0)),
            currency_code=datos.get("moneda", "USD"),
        )
        captura       = self._paypal.capture_order(orden["id"])
        self._order_id = orden["id"]
        return {
            "exito":      captura["status"] == "COMPLETED",
            "mensaje":    f"Pago {captura['status']}",
            "referencia": self._order_id,
        }

    def obtener_estado(self) -> Dict[str, Any]:
        return {"conectado": self._conectado, "proveedor": "PayPal", "ultimo_pedido": self._order_id}


# ---------------------------------------------------------------------------
# MercadoPago
# ---------------------------------------------------------------------------

class MercadoPagoAPI:
    """Simulación del SDK de MercadoPago."""

    def __init__(self, access_token: str):
        self.access_token = access_token

    def preference_create(self, items: list) -> dict:
        print(f"[MercadoPago] Creando preferencia con {len(items)} ítem(s)")
        return {"id": f"MP-PREF-{len(items)}", "init_point": "https://mp.example.com/checkout"}

    def payment_get(self, payment_id: str) -> dict:
        return {"id": payment_id, "status": "approved", "status_detail": "accredited"}


class AdaptadorMercadoPago(IServicioExterno):
    """Adapta MercadoPagoAPI a IServicioExterno."""

    def __init__(self, access_token: str = "TEST-TOKEN-DEMO"):
        self._mp          = MercadoPagoAPI(access_token)
        self._conectado   = False
        self._pref_id     = ""

    def conectar(self) -> bool:
        self._conectado = self._mp.access_token.startswith("TEST-") or \
                          self._mp.access_token.startswith("APP_USR-")
        return self._conectado

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {titulo, monto, moneda}
        """
        items = [{
            "title":        datos.get("titulo", "Evento"),
            "unit_price":   datos.get("monto", 0),
            "quantity":     1,
            "currency_id":  datos.get("moneda", "ARS"),
        }]
        pref           = self._mp.preference_create(items)
        self._pref_id  = pref["id"]
        return {
            "exito":      True,
            "mensaje":    "Preferencia creada",
            "referencia": self._pref_id,
            "url_pago":   pref["init_point"],
        }

    def obtener_estado(self) -> Dict[str, Any]:
        estado = {}
        if self._pref_id:
            estado = self._mp.payment_get(self._pref_id)
        return {"conectado": self._conectado, "proveedor": "MercadoPago", "ultimo_pago": estado}


# ===========================================================================
# STREAMING
# ===========================================================================

# ---------------------------------------------------------------------------
# YouTube Live
# ---------------------------------------------------------------------------

class YouTubeStreamAPI:
    """Simulación de la YouTube Data API v3 para streaming en vivo."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def broadcasts_insert(self, title: str, scheduled_start: str) -> dict:
        return {"id": f"YT-{title[:6].upper()}", "status": {"lifeCycleStatus": "created"}}

    def streams_insert(self, title: str) -> dict:
        return {"id": f"YTS-{title[:4].upper()}", "cdn": {"ingestionAddress": "rtmp://a.rtmp.youtube.com/live2"}}

    def broadcasts_bind(self, broadcast_id: str, stream_id: str) -> dict:
        return {"id": broadcast_id, "contentDetails": {"boundStreamId": stream_id}}


class AdaptadorYouTube(IServicioExterno):
    """Adapta YouTubeStreamAPI a IServicioExterno."""

    def __init__(self, api_key: str = "YT_API_KEY_DEMO"):
        self._yt            = YouTubeStreamAPI(api_key)
        self._conectado     = False
        self._broadcast_id  = ""

    def conectar(self) -> bool:
        self._conectado = bool(self._yt.api_key)
        print("[YouTube] Conectado")
        return self._conectado

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {titulo, fecha_inicio}
        """
        broadcast = self._yt.broadcasts_insert(
            title=datos.get("titulo", "Evento en vivo"),
            scheduled_start=str(datos.get("fecha_inicio", "")),
        )
        stream = self._yt.streams_insert(title=datos.get("titulo", "Stream"))
        self._yt.broadcasts_bind(broadcast["id"], stream["id"])
        self._broadcast_id = broadcast["id"]
        return {
            "exito":       True,
            "mensaje":     "Transmisión configurada en YouTube",
            "referencia":  self._broadcast_id,
            "rtmp_url":    stream["cdn"]["ingestionAddress"],
        }

    def obtener_estado(self) -> Dict[str, Any]:
        return {"conectado": self._conectado, "proveedor": "YouTube Live", "broadcast_id": self._broadcast_id}


# ---------------------------------------------------------------------------
# Vimeo
# ---------------------------------------------------------------------------

class VimeoStreamAPI:
    """Simulación del API de Vimeo para streaming en vivo."""

    def __init__(self, access_token: str):
        self.access_token = access_token

    def create_live_event(self, title: str) -> dict:
        return {"uri": f"/live_events/{title[:5].lower()}001", "stream_key": "SK-VIMEO-DEMO"}

    def get_status(self, uri: str) -> dict:
        return {"uri": uri, "status": "ready"}


class AdaptadorVimeo(IServicioExterno):
    """Adapta VimeoStreamAPI a IServicioExterno."""

    def __init__(self, access_token: str = "VIMEO_TOKEN_DEMO"):
        self._vimeo       = VimeoStreamAPI(access_token)
        self._conectado   = False
        self._event_uri   = ""

    def conectar(self) -> bool:
        self._conectado = bool(self._vimeo.access_token)
        print(f"[Vimeo] Conectado")
        return self._conectado

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {titulo}
        """
        evento = self._vimeo.create_live_event(datos.get("titulo", "Evento"))
        self._event_uri = evento["uri"]
        return {
            "exito":      True,
            "mensaje":    "Evento en vivo creado en Vimeo",
            "referencia": self._event_uri,
            "stream_key": evento["stream_key"],
        }

    def obtener_estado(self) -> Dict[str, Any]:
        estado = {}
        if self._event_uri:
            estado = self._vimeo.get_status(self._event_uri)
        return {"conectado": self._conectado, "proveedor": "Vimeo", "evento": estado}


# ---------------------------------------------------------------------------
# Facebook Live
# ---------------------------------------------------------------------------

class FacebookLiveAPI:
    """Simulación del Graph API de Facebook para Live Video."""

    def __init__(self, page_access_token: str):
        self.page_access_token = page_access_token

    def create_live_video(self, title: str, description: str) -> dict:
        return {
            "id":           f"FB-{title[:4].upper()}-777",
            "stream_url":   "rtmps://live-api-s.facebook.com:443/rtmp/",
            "secure_stream_url": "rtmps://live-api-s.facebook.com:443/rtmp/",
        }

    def get_live_video(self, video_id: str) -> dict:
        return {"id": video_id, "status": "LIVE_STOPPED", "live_status": "SCHEDULED"}


class AdaptadorFacebookLive(IServicioExterno):
    """Adapta FacebookLiveAPI a IServicioExterno."""

    def __init__(self, page_access_token: str = "FB_PAGE_TOKEN_DEMO"):
        self._fb         = FacebookLiveAPI(page_access_token)
        self._conectado  = False
        self._video_id   = ""

    def conectar(self) -> bool:
        self._conectado = bool(self._fb.page_access_token)
        print("[Facebook Live] Conectado")
        return self._conectado

    def procesar_solicitud(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        datos esperados: {titulo, descripcion}
        """
        video = self._fb.create_live_video(
            title=datos.get("titulo", "Evento"),
            description=datos.get("descripcion", ""),
        )
        self._video_id = video["id"]
        return {
            "exito":      True,
            "mensaje":    "Live video creado en Facebook",
            "referencia": self._video_id,
            "rtmp_url":   video["stream_url"],
        }

    def obtener_estado(self) -> Dict[str, Any]:
        estado = {}
        if self._video_id:
            estado = self._fb.get_live_video(self._video_id)
        return {"conectado": self._conectado, "proveedor": "Facebook Live", "video": estado}


# ---------------------------------------------------------------------------
# Función de conveniencia: procesar con cualquier proveedor
# ---------------------------------------------------------------------------

def procesar_con_proveedor(proveedor: IServicioExterno, datos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función genérica que usa la interfaz uniforme.
    El caller no necesita saber qué proveedor concreto está usando.
    """
    if not proveedor.conectar():
        return {"exito": False, "mensaje": f"No se pudo conectar con {proveedor.nombre_proveedor}"}
    return proveedor.procesar_solicitud(datos)


# ---------------------------------------------------------------------------
# Ejemplo de uso (ejecutar directamente: python adapter.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("EJEMPLO: Pasarelas de pago con interfaz uniforme")
    print("=" * 60)

    pasarelas = [
        AdaptadorStripe(api_key="sk_test_demo"),
        AdaptadorPayPal(client_id="CLIENT_ID", client_secret="CLIENT_SECRET"),
        AdaptadorMercadoPago(access_token="TEST-TOKEN-DEMO"),
    ]
    datos_pago = {"monto": 500.00, "moneda": "USD", "titulo": "Entrada Conferencia"}

    for pasarela in pasarelas:
        resultado = procesar_con_proveedor(pasarela, datos_pago)
        print(f"\n[{pasarela.nombre_proveedor}] → {resultado}")

    print("\n" + "=" * 60)
    print("EJEMPLO: Plataformas de streaming con interfaz uniforme")
    print("=" * 60)

    plataformas = [
        AdaptadorYouTube(),
        AdaptadorVimeo(),
        AdaptadorFacebookLive(),
    ]
    datos_stream = {"titulo": "Conferencia Tech 2025", "fecha_inicio": "2025-06-01T09:00:00", "descripcion": "Demo"}

    for plataforma in plataformas:
        resultado = procesar_con_proveedor(plataforma, datos_stream)
        print(f"\n[{plataforma.nombre_proveedor}] → {resultado}")


# ── Payment Gateway Adapters (Professional System) ───────────────────────────
import random
from abc import ABC, abstractmethod
from datetime import datetime


class AdapterPasarela(ABC):
    """Common interface for all payment gateways."""

    @abstractmethod
    def procesar(self, monto: float, datos_evento: dict) -> dict:
        """Processes a payment and returns the result."""
        pass

    @abstractmethod
    def obtener_nombre(self) -> str:
        pass

    @abstractmethod
    def obtener_icono(self) -> str:
        pass


class StripeAdapter(AdapterPasarela):
    """Adapter for Stripe payment gateway (simulated)."""

    def procesar(self, monto: float, datos_evento: dict) -> dict:
        return {
            'exitoso': True,
            'referencia': f"STRIPE-{datetime.now().strftime('%Y%m%d')}-{random.randint(100000, 999999)}",
            'mensaje': 'Pago procesado exitosamente con Stripe',
        }

    def obtener_nombre(self) -> str:
        return "Stripe"

    def obtener_icono(self) -> str:
        return "💳"


class PayPalAdapter(AdapterPasarela):
    """Adapter for PayPal payment gateway (simulated)."""

    def procesar(self, monto: float, datos_evento: dict) -> dict:
        return {
            'exitoso': True,
            'referencia': f"PAYPAL-{datetime.now().strftime('%Y%m%d')}-{random.randint(100000, 999999)}",
            'mensaje': 'Pago procesado exitosamente con PayPal',
        }

    def obtener_nombre(self) -> str:
        return "PayPal"

    def obtener_icono(self) -> str:
        return "🅿️"


class MercadoPagoAdapter(AdapterPasarela):
    """Adapter for MercadoPago payment gateway (simulated)."""

    def procesar(self, monto: float, datos_evento: dict) -> dict:
        return {
            'exitoso': True,
            'referencia': f"MERCADOPAGO-{datetime.now().strftime('%Y%m%d')}-{random.randint(100000, 999999)}",
            'mensaje': 'Pago procesado exitosamente con MercadoPago',
        }

    def obtener_nombre(self) -> str:
        return "MercadoPago"

    def obtener_icono(self) -> str:
        return "💰"


# Registry: maps Pasarela.tipo to an AdapterPasarela instance
_ADAPTER_MAP: dict = {
    'stripe':      StripeAdapter,
    'paypal':      PayPalAdapter,
    'mercadopago': MercadoPagoAdapter,
}


def get_adapter_for_pasarela(tipo: str) -> AdapterPasarela:
    """Returns the appropriate AdapterPasarela instance for the given gateway type."""
    cls = _ADAPTER_MAP.get(tipo)
    if cls is None:
        raise ValueError(f"No adapter found for gateway type: {tipo}")
    return cls()
