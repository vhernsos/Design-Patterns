from abc import ABC, abstractmethod
from typing import Dict, Any, List


class PaymentProvider(ABC):
    @abstractmethod
    def create_payment(self, amount: float, currency: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def confirm_payment(self, payment_id: str) -> bool:
        pass

    @abstractmethod
    def refund_payment(self, payment_id: str) -> bool:
        pass


class StripePaymentProvider(PaymentProvider):
    def create_payment(self, amount: float, currency: str) -> Dict[str, Any]:
        return {
            "provider": "stripe",
            "amount": amount,
            "currency": currency,
            "status": "pending",
            "client_secret": f"sk_test_{amount}_{currency}"
        }

    def confirm_payment(self, payment_id: str) -> bool:
        return True

    def refund_payment(self, payment_id: str) -> bool:
        return True


class PayPalPaymentProvider(PaymentProvider):
    def create_payment(self, amount: float, currency: str) -> Dict[str, Any]:
        return {
            "provider": "paypal",
            "amount": amount,
            "currency": currency,
            "status": "pending",
            "approval_url": f"https://paypal.com/approve?amount={amount}"
        }

    def confirm_payment(self, payment_id: str) -> bool:
        return True

    def refund_payment(self, payment_id: str) -> bool:
        return True


class VenueProvider(ABC):
    @abstractmethod
    def check_availability(self, date: str, guests: int) -> bool:
        pass

    @abstractmethod
    def book_venue(self, date: str, guests: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_booking(self, booking_id: str) -> bool:
        pass


class BallroomVenueProvider(VenueProvider):
    def check_availability(self, date: str, guests: int) -> bool:
        return True

    def book_venue(self, date: str, guests: int) -> Dict[str, Any]:
        return {
            "venue_type": "ballroom",
            "booking_id": f"BR-{date}-{guests}",
            "status": "confirmed",
            "capacity": 500
        }

    def cancel_booking(self, booking_id: str) -> bool:
        return True


class GardenVenueProvider(VenueProvider):
    def check_availability(self, date: str, guests: int) -> bool:
        return True

    def book_venue(self, date: str, guests: int) -> Dict[str, Any]:
        return {
            "venue_type": "garden",
            "booking_id": f"GD-{date}-{guests}",
            "status": "confirmed",
            "capacity": 300
        }

    def cancel_booking(self, booking_id: str) -> bool:
        return True


class CateringProvider(ABC):
    @abstractmethod
    def get_menu_options(self) -> List[str]:
        pass

    @abstractmethod
    def create_order(self, menu: str, guests: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass


class TraditionalCateringProvider(CateringProvider):
    def get_menu_options(self) -> List[str]:
        return ["Spanish Traditional", "International", "Mediterranean"]

    def create_order(self, menu: str, guests: int) -> Dict[str, Any]:
        return {
            "provider": "traditional_catering",
            "menu": menu,
            "guests": guests,
            "order_id": f"TC-{menu[:3]}-{guests}",
            "status": "confirmed"
        }

    def cancel_order(self, order_id: str) -> bool:
        return True


class VeganCateringProvider(CateringProvider):
    def get_menu_options(self) -> List[str]:
        return ["Vegan Fusion", "Plant-Based Gourmet", "Raw Vegan"]

    def create_order(self, menu: str, guests: int) -> Dict[str, Any]:
        return {
            "provider": "vegan_catering",
            "menu": menu,
            "guests": guests,
            "order_id": f"VC-{menu[:3]}-{guests}",
            "status": "confirmed"
        }

    def cancel_order(self, order_id: str) -> bool:
        return True


class ServiceFactory:
    _payment_providers = {
        'stripe': StripePaymentProvider,
        'paypal': PayPalPaymentProvider,
    }
    
    _venue_providers = {
        'ballroom': BallroomVenueProvider,
        'garden': GardenVenueProvider,
    }
    
    _catering_providers = {
        'traditional': TraditionalCateringProvider,
        'vegan': VeganCateringProvider,
    }

    @staticmethod
    def create_payment_provider(provider_type: str) -> PaymentProvider:
        if provider_type not in ServiceFactory._payment_providers:
            raise ValueError(f"Unknown payment provider: {provider_type}")
        return ServiceFactory._payment_providers[provider_type]()

    @staticmethod
    def create_venue_provider(provider_type: str) -> VenueProvider:
        if provider_type not in ServiceFactory._venue_providers:
            raise ValueError(f"Unknown venue provider: {provider_type}")
        return ServiceFactory._venue_providers[provider_type]()

    @staticmethod
    def create_catering_provider(provider_type: str) -> CateringProvider:
        if provider_type not in ServiceFactory._catering_providers:
            raise ValueError(f"Unknown catering provider: {provider_type}")
        return ServiceFactory._catering_providers[provider_type]()

    @staticmethod
    def get_available_payment_providers() -> List[str]:
        return list(ServiceFactory._payment_providers.keys())

    @staticmethod
    def get_available_venue_providers() -> List[str]:
        return list(ServiceFactory._venue_providers.keys())

    @staticmethod
    def get_available_catering_providers() -> List[str]:
        return list(ServiceFactory._catering_providers.keys())
