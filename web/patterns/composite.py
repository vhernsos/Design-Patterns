
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional


                                                                             
                                                  
                                                                             

class ComponenteEvento(ABC):

    def __init__(self, nombre: str):
        self.nombre = nombre

                                                                    

    @abstractmethod
    def calcular_presupuesto(self) -> float:
        pass

    @abstractmethod
    def calcular_duracion(self) -> float:
        pass

    @abstractmethod
    def obtener_capacidad(self) -> int:
        pass

    @abstractmethod
    def mover_fechas(self, delta: timedelta) -> None:
        pass

    @abstractmethod
    def obtener_resumen(self, nivel: int = 0) -> str:
        pass

    @abstractmethod
    def es_compuesto(self) -> bool:
        pass

    def __str__(self) -> str:
        return self.obtener_resumen()


                                                                             
                          
                                                                             

class EventoSimple(ComponenteEvento):

    def __init__(
        self,
        nombre: str,
        presupuesto: float = 0.0,
        duracion_horas: float = 1.0,
        capacidad: int = 100,
        fecha_inicio: Optional[datetime] = None,
        descripcion: str = "",
        tipo: str = "",
    ):
        super().__init__(nombre)
        self.presupuesto    = presupuesto
        self.duracion_horas = duracion_horas
        self.capacidad      = capacidad
        self.fecha_inicio   = fecha_inicio
        self.descripcion    = descripcion
        self.tipo           = tipo

    @property
    def fecha_fin(self) -> Optional[datetime]:
        if self.fecha_inicio:
            return self.fecha_inicio + timedelta(hours=self.duracion_horas)
        return None

    def calcular_presupuesto(self) -> float:
        return self.presupuesto

    def calcular_duracion(self) -> float:
        return self.duracion_horas

    def obtener_capacidad(self) -> int:
        return self.capacidad

    def mover_fechas(self, delta: timedelta) -> None:
        if self.fecha_inicio:
            self.fecha_inicio += delta

    def es_compuesto(self) -> bool:
        return False

    def obtener_resumen(self, nivel: int = 0) -> str:
        sangria    = "  " * nivel
        inicio_str = self.fecha_inicio.strftime("%Y-%m-%d %H:%M") if self.fecha_inicio else "Sin fecha"
        return (
            f"{sangria}🎵 {self.nombre}"
            f" | Presupuesto: ${self.presupuesto:,.0f}"
            f" | Duración: {self.duracion_horas}h"
            f" | Capacidad: {self.capacidad}"
            f" | Inicio: {inicio_str}"
        )


                                                                             
                                
                                                                             

class EventoCompuesto(ComponenteEvento):

    def __init__(
        self,
        nombre: str,
        descripcion: str = "",
        fecha_inicio: Optional[datetime] = None,
    ):
        super().__init__(nombre)
        self.descripcion  = descripcion
        self.fecha_inicio = fecha_inicio
        self._hijos: List[ComponenteEvento] = []

                              

    def agregar(self, componente: ComponenteEvento) -> 'EventoCompuesto':
        self._hijos.append(componente)
        return self

    def eliminar(self, componente: ComponenteEvento) -> bool:
        if componente in self._hijos:
            self._hijos.remove(componente)
            return True
        return False

    def obtener_hijos(self) -> List[ComponenteEvento]:
        return list(self._hijos)

    def esta_vacio(self) -> bool:
        return len(self._hijos) == 0

                                    

    def calcular_presupuesto(self) -> float:
        return sum(hijo.calcular_presupuesto() for hijo in self._hijos)

    def calcular_duracion(self) -> float:
        return sum(hijo.calcular_duracion() for hijo in self._hijos)

    def obtener_capacidad(self) -> int:
        if not self._hijos:
            return 0
        return max(hijo.obtener_capacidad() for hijo in self._hijos)

    def mover_fechas(self, delta: timedelta) -> None:
        if self.fecha_inicio:
            self.fecha_inicio += delta
        for hijo in self._hijos:
            hijo.mover_fechas(delta)

    def es_compuesto(self) -> bool:
        return True

    def obtener_resumen(self, nivel: int = 0) -> str:
        sangria    = "  " * nivel
        inicio_str = self.fecha_inicio.strftime("%Y-%m-%d") if self.fecha_inicio else "Sin fecha"
        lineas = [
            f"{sangria}📅 {self.nombre}"
            f" | Presupuesto total: ${self.calcular_presupuesto():,.0f}"
            f" | Duración total: {self.calcular_duracion()}h"
            f" | Capacidad máx: {self.obtener_capacidad()}"
            f" | Inicio: {inicio_str}"
        ]
        for hijo in self._hijos:
            lineas.append(hijo.obtener_resumen(nivel + 1))
        return "\n".join(lineas)

    def contar_eventos(self) -> int:
        total = 0
        for hijo in self._hijos:
            if hijo.es_compuesto():
                total += hijo.contar_eventos()                               
            else:
                total += 1
        return total

    def buscar(self, nombre: str) -> Optional[ComponenteEvento]:
        for hijo in self._hijos:
            if hijo.nombre == nombre:
                return hijo
            if hijo.es_compuesto():
                encontrado = hijo.buscar(nombre)                               
                if encontrado:
                    return encontrado
        return None


                                                                             
                                                               
                                                                             

def crear_festival_musica(nombre: str, fecha_inicio: datetime) -> EventoCompuesto:
    festival = EventoCompuesto(nombre, fecha_inicio=fecha_inicio)

    for num_dia in range(1, 4):
        fecha_dia = fecha_inicio + timedelta(days=num_dia - 1)
        dia = EventoCompuesto(f"Día {num_dia}", fecha_inicio=fecha_dia)

        dia.agregar(EventoSimple(
            f"Concierto Apertura Día {num_dia}",
            presupuesto=5_000,
            duracion_horas=2,
            capacidad=2_000,
            fecha_inicio=fecha_dia.replace(hour=18),
        ))
        dia.agregar(EventoSimple(
            f"Concierto Estelar Día {num_dia}",
            presupuesto=10_000,
            duracion_horas=3,
            capacidad=2_000,
            fecha_inicio=fecha_dia.replace(hour=21),
        ))
        festival.agregar(dia)

    return festival


def crear_cumbre_empresarial(nombre: str, fecha_inicio: datetime) -> EventoCompuesto:
    cumbre = EventoCompuesto(nombre, fecha_inicio=fecha_inicio)

    keynotes = EventoCompuesto("Keynotes", fecha_inicio=fecha_inicio.replace(hour=9))
    keynotes.agregar(EventoSimple("Apertura CEO",          presupuesto=2_000, duracion_horas=1, capacidad=500, fecha_inicio=fecha_inicio.replace(hour=9)))
    keynotes.agregar(EventoSimple("Conferencia Principal", presupuesto=5_000, duracion_horas=2, capacidad=500, fecha_inicio=fecha_inicio.replace(hour=10)))

    talleres = EventoCompuesto("Talleres Paralelos", fecha_inicio=fecha_inicio.replace(hour=14))
    talleres.agregar(EventoSimple("Taller IA",           presupuesto=1_500, duracion_horas=2, capacidad=100, fecha_inicio=fecha_inicio.replace(hour=14)))
    talleres.agregar(EventoSimple("Taller Cloud",        presupuesto=1_500, duracion_horas=2, capacidad=100, fecha_inicio=fecha_inicio.replace(hour=14)))
    talleres.agregar(EventoSimple("Taller Liderazgo",    presupuesto=1_200, duracion_horas=2, capacidad=80,  fecha_inicio=fecha_inicio.replace(hour=14)))

    networking = EventoSimple("Networking & Cocktail", presupuesto=3_000, duracion_horas=2, capacidad=500, fecha_inicio=fecha_inicio.replace(hour=17))

    cumbre.agregar(keynotes).agregar(talleres).agregar(networking)
    return cumbre


def crear_boda(nombre: str, fecha_inicio: datetime) -> EventoCompuesto:
    boda = EventoCompuesto(nombre, fecha_inicio=fecha_inicio)

    boda.agregar(EventoSimple(
        "Ceremonia",
        presupuesto=8_000, duracion_horas=1.5, capacidad=200,
        fecha_inicio=fecha_inicio.replace(hour=13),
    ))
    boda.agregar(EventoSimple(
        "Recepción y Banquete",
        presupuesto=20_000, duracion_horas=5, capacidad=200,
        fecha_inicio=fecha_inicio.replace(hour=15),
    ))
    boda.agregar(EventoSimple(
        "Desayuno del día siguiente",
        presupuesto=4_000, duracion_horas=2, capacidad=50,
        fecha_inicio=(fecha_inicio + timedelta(days=1)).replace(hour=10),
    ))
    return boda


                                                                             
                                                             
                                                                             

if __name__ == "__main__":
    print("=" * 70)
    print("EJEMPLO 1: Festival de Música")
    print("=" * 70)
    festival = crear_festival_musica("Festival Rock 2025", datetime(2025, 7, 1))
    print(festival.obtener_resumen())
    print(f"\nTotal eventos (hojas): {festival.contar_eventos()}")
    print(f"Presupuesto total:     ${festival.calcular_presupuesto():,.0f}")
    print(f"Duración total:        {festival.calcular_duracion()} horas")
    print(f"Capacidad máxima:      {festival.obtener_capacidad()} personas")

    print("\n--- Moviendo el festival 14 días ---")
    festival.mover_fechas(timedelta(days=14))
    dia1 = festival.obtener_hijos()[0]
    print(f"Nueva fecha del Día 1: {dia1.fecha_inicio}")

    print("\n" + "=" * 70)
    print("EJEMPLO 2: Cumbre Empresarial")
    print("=" * 70)
    cumbre = crear_cumbre_empresarial("Tech Summit 2025", datetime(2025, 9, 15))
    print(cumbre.obtener_resumen())

    print("\n" + "=" * 70)
    print("EJEMPLO 3: Boda")
    print("=" * 70)
    boda = crear_boda("Boda García-López", datetime(2025, 11, 8))
    print(boda.obtener_resumen())
    print(f"\nPresupuesto total boda: ${boda.calcular_presupuesto():,.0f}")

    print("\n" + "=" * 70)
    print("EJEMPLO 4: Buscar sub-evento por nombre")
    print("=" * 70)
    encontrado = cumbre.buscar("Taller IA")
    if encontrado:
        print(f"Encontrado: {encontrado.obtener_resumen()}")
