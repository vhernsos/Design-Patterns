from abc import ABC, abstractmethod
from typing import Dict, Any, List


class EventFacade:
    def __init__(self):
        self._event_service = EventService()
        self._payment_service = PaymentService()
        self._notification_service = NotificationService()
        self._vendor_service = VendorService()

    def create_complete_event(self, event_data: Dict[str, Any], payment_method: str, 
                             vendors: List[str], notify_email: str) -> Dict[str, Any]:
        result = {
            "success": True,
            "steps": []
        }

        event_id = self._event_service.create_event(event_data)
        result["event_id"] = event_id
        result["steps"].append(f"Event created: {event_id}")

        payment_result = self._payment_service.process_payment(
            event_id, event_data.get("budget", 0), payment_method
        )
        if payment_result["success"]:
            result["steps"].append("Payment processed successfully")
        else:
            result["success"] = False
            result["steps"].append("Payment failed")
            return result

        for vendor in vendors:
            vendor_result = self._vendor_service.assign_vendor(event_id, vendor)
            if vendor_result["success"]:
                result["steps"].append(f"Vendor assigned: {vendor}")

        notification_result = self._notification_service.send_notification(
            notify_email, f"Event {event_id} created successfully"
        )
        if notification_result["success"]:
            result["steps"].append("Notification sent")

        return result

    def cancel_event(self, event_id: str) -> Dict[str, Any]:
        result = {
            "success": True,
            "steps": []
        }

        self._vendor_service.unassign_all_vendors(event_id)
        result["steps"].append("All vendors unassigned")

        self._payment_service.refund_payment(event_id)
        result["steps"].append("Payment refunded")

        self._event_service.delete_event(event_id)
        result["steps"].append("Event deleted")

        return result


class EventService:
    def create_event(self, event_data: Dict[str, Any]) -> str:
        event_id = f"EVT-{event_data.get('name', 'Unknown')[:3]}"
        return event_id

    def delete_event(self, event_id: str) -> bool:
        return True

    def get_event(self, event_id: str) -> Dict[str, Any]:
        return {"id": event_id, "status": "active"}


class PaymentService:
    def process_payment(self, event_id: str, amount: float, method: str) -> Dict[str, Any]:
        return {
            "success": True,
            "payment_id": f"PAY-{event_id}",
            "amount": amount,
            "method": method,
            "status": "completed"
        }

    def refund_payment(self, event_id: str) -> Dict[str, Any]:
        return {
            "success": True,
            "refund_id": f"REF-{event_id}",
            "status": "processed"
        }


class NotificationService:
    def send_notification(self, email: str, message: str) -> Dict[str, Any]:
        return {
            "success": True,
            "email": email,
            "message": message,
            "sent_at": "2024-01-01T00:00:00"
        }

    def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        return {
            "success": True,
            "phone": phone,
            "message": message,
            "sent_at": "2024-01-01T00:00:00"
        }


class VendorService:
    def assign_vendor(self, event_id: str, vendor_name: str) -> Dict[str, Any]:
        return {
            "success": True,
            "event_id": event_id,
            "vendor": vendor_name,
            "status": "assigned"
        }

    def unassign_vendor(self, event_id: str, vendor_name: str) -> Dict[str, Any]:
        return {
            "success": True,
            "event_id": event_id,
            "vendor": vendor_name,
            "status": "unassigned"
        }

    def unassign_all_vendors(self, event_id: str) -> Dict[str, Any]:
        return {
            "success": True,
            "event_id": event_id,
            "status": "all_vendors_unassigned"
        }

    def get_available_vendors(self) -> List[str]:
        return ["Vendor A", "Vendor B", "Vendor C", "Catering Co", "Streaming Pro"]
