from abc import ABC, abstractmethod
from typing import Dict, Any, List


class EventFilterStrategy(ABC):
    @abstractmethod
    def filter(self, events: List[Dict[str, Any]], criteria: Any) -> List[Dict[str, Any]]:
        pass


class FilterByDate(EventFilterStrategy):
    def filter(self, events: List[Dict[str, Any]], criteria: str) -> List[Dict[str, Any]]:
        return [e for e in events if e.get('date') == criteria]


class FilterByBudget(EventFilterStrategy):
    def filter(self, events: List[Dict[str, Any]], criteria: float) -> List[Dict[str, Any]]:
        return [e for e in events if float(e.get('budget', 0)) <= criteria]


class FilterByLocation(EventFilterStrategy):
    def filter(self, events: List[Dict[str, Any]], criteria: str) -> List[Dict[str, Any]]:
        return [e for e in events if e.get('location') == criteria]


class FilterByAttendees(EventFilterStrategy):
    def filter(self, events: List[Dict[str, Any]], criteria: int) -> List[Dict[str, Any]]:
        return [e for e in events if int(e.get('attendees', 0)) <= criteria]


class CostCalculationStrategy(ABC):
    @abstractmethod
    def calculate(self, base_cost: float, services: List[str]) -> float:
        pass


class StandardCostCalculation(CostCalculationStrategy):
    def calculate(self, base_cost: float, services: List[str]) -> float:
        multiplier = 1.0 + (len(services) * 0.1)
        return base_cost * multiplier


class PremiumCostCalculation(CostCalculationStrategy):
    def calculate(self, base_cost: float, services: List[str]) -> float:
        multiplier = 1.0 + (len(services) * 0.15)
        return base_cost * multiplier


class BudgetCostCalculation(CostCalculationStrategy):
    def calculate(self, base_cost: float, services: List[str]) -> float:
        multiplier = 1.0 + (len(services) * 0.05)
        return base_cost * multiplier


class EventFilter:
    def __init__(self, strategy: EventFilterStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: EventFilterStrategy):
        self._strategy = strategy

    def apply_filter(self, events: List[Dict[str, Any]], criteria: Any) -> List[Dict[str, Any]]:
        return self._strategy.filter(events, criteria)


class CostCalculator:
    def __init__(self, strategy: CostCalculationStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: CostCalculationStrategy):
        self._strategy = strategy

    def calculate_cost(self, base_cost: float, services: List[str]) -> float:
        return self._strategy.calculate(base_cost, services)
