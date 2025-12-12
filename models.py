from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class User:
    email: str
    password: str


class UserRegistry:
    """
    Simple in-memory user registry with basic validation logic.
    """

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}

    def _is_valid_email(self, email: str) -> bool:
        # very small validation just for tests
        return "@" in email and "." in email.split("@")[-1]

    def _is_strong_password(self, password: str) -> bool:
        return len(password) >= 6

    def register(self, email: str, password: str, confirm_password: str) -> Dict[str, str]:
        if not self._is_valid_email(email):
            return {"success": False, "message": "Invalid email format"}
        if password != confirm_password:
            return {"success": False, "message": "Passwords do not match"}
        if not self._is_strong_password(password):
            return {"success": False, "message": "Password too weak"}
        if email in self._users:
            return {"success": False, "message": "Email already registered"}

        self._users[email] = User(email=email, password=password)
        return {"success": True, "message": "Registration successful, confirmation email sent"}

    def is_registered(self, email: str) -> bool:
        return email in self._users


@dataclass
class Restaurant:
    name: str
    cuisine: str
    location: str
    rating: float


class RestaurantDatabase:
    def __init__(self) -> None:
        self._restaurants: List[Restaurant] = []

    def add_restaurant(self, restaurant: Restaurant) -> None:
        self._restaurants.append(restaurant)

    def all(self) -> List[Restaurant]:
        return list(self._restaurants)


class RestaurantBrowsing:
    """
    Provides filtering over RestaurantDatabase
    """

    def __init__(self, db: RestaurantDatabase) -> None:
        self.db = db

    def search(
        self,
        cuisine: Optional[str] = None,
        location: Optional[str] = None,
        min_rating: Optional[float] = None,
    ) -> List[Restaurant]:
        results = []
        for r in self.db.all():
            if cuisine and r.cuisine != cuisine:
                continue
            if location and r.location != location:
                continue
            if min_rating is not None and r.rating < min_rating:
                continue
            results.append(r)
        return results


@dataclass
class CartItem:
    name: str
    price: float
    quantity: int = 1


class Cart:
    def __init__(self) -> None:
        self.items: Dict[str, CartItem] = {}

    def add_item(self, name: str, price: float, quantity: int = 1) -> None:
        if name in self.items:
            self.items[name].quantity += quantity
        else:
            self.items[name] = CartItem(name=name, price=price, quantity=quantity)

    def remove_item(self, name: str) -> None:
        self.items.pop(name, None)

    def total(self) -> float:
        return sum(item.price * item.quantity for item in self.items.values())

    def is_empty(self) -> bool:
        return not self.items


class RestaurantMenu:
    """
    Holds available menu items for a restaurant.
    """

    def __init__(self) -> None:
        self.available_items: Dict[str, float] = {}

    def add_menu_item(self, name: str, price: float) -> None:
        self.available_items[name] = price

    def has_item(self, name: str) -> bool:
        return name in self.available_items


class OrderPlacement:
    """
    Validates and confirms orders using Cart and RestaurantMenu.
    """

    def __init__(self, cart: Cart, menu: RestaurantMenu) -> None:
        self.cart = cart
        self.menu = menu

    def validate_order(self) -> Dict[str, object]:
        if self.cart.is_empty():
            return {"success": False, "message": "Cart is empty"}

        for item in self.cart.items.values():
            if not self.menu.has_item(item.name):
                return {
                    "success": False,
                    "message": f"{item.name} is not available",
                }

        return {"success": True, "message": "Order is valid"}


class PaymentMethod:
    """
    Represents an external payment processor. In production this might talk
    to an external service, but in tests we usually mock process_payment.
    """

    def process_payment(self, amount: float, payload: Dict[str, str]) -> bool:
        # placeholder implementation; real logic is outside scope
        # Always succeeds here – tests can override using mocks.
        return True


class PaymentProcessing:
    SUPPORTED_METHODS = {"credit_card"}

    def __init__(self, payment_method: PaymentMethod) -> None:
        self.payment_method = payment_method

    def validate_payment_method(self, method: str) -> bool:
        if method not in self.SUPPORTED_METHODS:
            raise ValueError("Invalid payment method")
        return True

    def validate_credit_card(self, card_number: str, cvv: str) -> bool:
        return len(card_number) in (15, 16) and len(cvv) == 3 and card_number.isdigit() and cvv.isdigit()

    def process_payment(
        self, amount: float, method: str, card_number: str, cvv: str
    ) -> str:
        try:
            self.validate_payment_method(method)
        except ValueError as exc:
            return f"Error: {exc}"

        if not self.validate_credit_card(card_number, cvv):
            return "Payment failed, please try again"

        success = self.payment_method.process_payment(
            amount,
            {"card_number": card_number, "cvv": cvv, "method": method},
        )
        if success:
            return "Payment successful, Order confirmed"
        return "Payment failed, please try again"


class OrderHistory:
    def __init__(self) -> None:
        self.orders: List[Dict[str, object]] = []

    def add_order(self, order_id: str, items, total: float, status: str, date: str) -> None:
        order = {
            "order_id": order_id,
            "items": items,
            "total": total,
            "status": status,
            "date": date,
        }
        self.orders.append(order)

    def view_order_history(self) -> List[Dict[str, object]]:
        return list(self.orders)

    def filter_orders(self, status: Optional[str] = None, date: Optional[str] = None) -> List[Dict[str, object]]:
        filtered_orders: List[Dict[str, object]] = []
        for order in self.orders:
            if status is not None and order["status"] != status:
                continue
            if date is not None and order["date"] != date:
                continue
            filtered_orders.append(order)
        return filtered_orders
