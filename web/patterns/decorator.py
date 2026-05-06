from abc import ABC, abstractmethod
from decimal import Decimal


class ComponenteEvento(ABC):
    """Interfaz base para evento y sus decoradores"""

    @abstractmethod
    def obtener_descripcion(self) -> str:
        pass

    @abstractmethod
    def obtener_precio(self) -> Decimal:
        pass

    @abstractmethod
    def obtener_nombre(self) -> str:
        pass


class EventoBase(ComponenteEvento):
    """Evento sin decoradores"""

    def __init__(self, evento_django):
        self.evento = evento_django

    def obtener_nombre(self) -> str:
        return self.evento.nombre

    def obtener_descripcion(self) -> str:
        return self.evento.descripcion or "Evento básico"

    def obtener_precio(self) -> Decimal:
        return self.evento.presupuesto or Decimal('0')


class DecoradorEvento(ComponenteEvento):
    """Clase base para todos los decoradores"""

    def __init__(self, componente: ComponenteEvento):
        self._componente = componente

    @abstractmethod
    def obtener_descripcion(self) -> str:
        pass

    @abstractmethod
    def obtener_precio(self) -> Decimal:
        pass

    def obtener_nombre(self) -> str:
        return self._componente.obtener_nombre()


# Decoradores concretos

class MusicaEnVivoDecorador(DecoradorEvento):
    """Añade música en vivo al evento – €2000"""
    PRECIO = Decimal('2000')
    NOMBRE = "Música en vivo"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Banda en vivo profesional"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class CateringPremiumDecorador(DecoradorEvento):
    """Añade catering premium – €3000"""
    PRECIO = Decimal('3000')
    NOMBRE = "Catering Premium"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Menú gourmet con camareros"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class SeguridadVIPDecorador(DecoradorEvento):
    """Añade seguridad VIP – €2000"""
    PRECIO = Decimal('2000')
    NOMBRE = "Seguridad VIP"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Equipo de seguridad VIP"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class StreamingAvanzadoDecorador(DecoradorEvento):
    """Añade streaming avanzado – €1500"""
    PRECIO = Decimal('1500')
    NOMBRE = "Streaming Avanzado"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Streaming 4K con múltiples ángulos"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class DJProfesionalDecorador(DecoradorEvento):
    """Añade DJ profesional – €1500"""
    PRECIO = Decimal('1500')
    NOMBRE = "DJ Profesional"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + DJ profesional todo el evento"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class IluminacionEspecialDecorador(DecoradorEvento):
    """Añade iluminación especial – €1200"""
    PRECIO = Decimal('1200')
    NOMBRE = "Iluminación Especial"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Sistema de iluminación LED profesional"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class OpenBarDecorador(DecoradorEvento):
    """Añade open bar – €2500"""
    PRECIO = Decimal('2500')
    NOMBRE = "Open Bar"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Open bar con bebidas premium"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class ValetParkingDecorador(DecoradorEvento):
    """Añade valet parking – €800"""
    PRECIO = Decimal('800')
    NOMBRE = "Valet Parking"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Servicio de valet parking"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class FotografoDecorador(DecoradorEvento):
    """Añade fotógrafo profesional – €1000"""
    PRECIO = Decimal('1000')
    NOMBRE = "Fotógrafo Profesional"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Fotógrafo profesional + álbum digital"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


class VideografoDecorador(DecoradorEvento):
    """Añade videógrafo profesional – €1200"""
    PRECIO = Decimal('1200')
    NOMBRE = "Videógrafo Profesional"

    def obtener_descripcion(self) -> str:
        return f"{self._componente.obtener_descripcion()} + Videógrafo profesional + edición"

    def obtener_precio(self) -> Decimal:
        return self._componente.obtener_precio() + self.PRECIO


# Registro de decoradores disponibles
DECORADORES_DISPONIBLES = {
    'musica_vivo':         MusicaEnVivoDecorador,
    'catering_premium':    CateringPremiumDecorador,
    'seguridad_vip':       SeguridadVIPDecorador,
    'streaming_avanzado':  StreamingAvanzadoDecorador,
    'dj_profesional':      DJProfesionalDecorador,
    'iluminacion':         IluminacionEspecialDecorador,
    'open_bar':            OpenBarDecorador,
    'valet_parking':       ValetParkingDecorador,
    'fotografo':           FotografoDecorador,
    'videografo':          VideografoDecorador,
}

# Human-readable labels
DECORADORES_LABELS = {
    'musica_vivo':         ('Música en vivo',         '2.000'),
    'catering_premium':    ('Catering Premium',        '3.000'),
    'seguridad_vip':       ('Seguridad VIP',           '2.000'),
    'streaming_avanzado':  ('Streaming Avanzado',      '1.500'),
    'dj_profesional':      ('DJ Profesional',          '1.500'),
    'iluminacion':         ('Iluminación Especial',    '1.200'),
    'open_bar':            ('Open Bar',                '2.500'),
    'valet_parking':       ('Valet Parking',           '800'),
    'fotografo':           ('Fotógrafo Profesional',   '1.000'),
    'videografo':          ('Videógrafo Profesional',  '1.200'),
}


def aplicar_decoradores(evento_django, lista_decoradores: list) -> ComponenteEvento:
    """Aplica decoradores en orden a un evento Django"""
    componente = EventoBase(evento_django)

    for decorador_key in lista_decoradores:
        if decorador_key in DECORADORES_DISPONIBLES:
            DecoradorClass = DECORADORES_DISPONIBLES[decorador_key]
            componente = DecoradorClass(componente)

    return componente
