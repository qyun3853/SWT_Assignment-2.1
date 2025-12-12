import unittest
from unittest.mock import MagicMock
from models import (
    UserRegistry,
    RestaurantDatabase,
    RestaurantBrowsing,
    Restaurant,
    Cart,
    RestaurantMenu,
    OrderPlacement,
    PaymentProcessing,
    PaymentMethod,
    OrderHistory,
)


class UserRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = UserRegistry()

    def test_successful_registration(self):
        result = self.registry.register("alice@example.com", "secret1", "secret1")
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Registration successful, confirmation email sent")
        self.assertTrue(self.registry.is_registered("alice@example.com"))

    def test_invalid_email(self):
        result = self.registry.register("aliceexample.com", "secret1", "secret1")
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid email format")

    def test_mismatched_passwords(self):
        result = self.registry.register("bob@example.com", "secret1", "secret2")
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Passwords do not match")

    def test_duplicate_email(self):
        self.registry.register("carol@example.com", "secret1", "secret1")
        result = self.registry.register("carol@example.com", "secret1", "secret1")
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Email already registered")


class RestaurantBrowsingTests(unittest.TestCase):
    def setUp(self):
        self.db = RestaurantDatabase()
        self.db.add_restaurant(Restaurant("Pizza Place", "Italian", "Downtown", 4.5))
        self.db.add_restaurant(Restaurant("Sushi Bar", "Japanese", "Downtown", 4.0))
        self.db.add_restaurant(Restaurant("Curry House", "Indian", "Uptown", 3.8))
        self.browsing = RestaurantBrowsing(self.db)

    def test_filter_by_cuisine(self):
        results = self.browsing.search(cuisine="Italian")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Pizza Place")

    def test_filter_by_location(self):
        results = self.browsing.search(location="Downtown")
        self.assertEqual(len(results), 2)

    def test_filter_by_rating(self):
        results = self.browsing.search(min_rating=4.2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Pizza Place")

    def test_combined_filters(self):
        results = self.browsing.search(cuisine="Japanese", location="Downtown", min_rating=4.0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Sushi Bar")


class CartAndOrderPlacementTests(unittest.TestCase):
    def setUp(self):
        self.cart = Cart()
        self.menu = RestaurantMenu()
        self.menu.add_menu_item("Pizza", 10.0)
        self.menu.add_menu_item("Burger", 8.5)
        self.order = OrderPlacement(self.cart, self.menu)

    def test_add_and_total_cart_items(self):
        self.cart.add_item("Pizza", 10.0, quantity=2)
        self.cart.add_item("Burger", 8.5, quantity=1)
        self.assertAlmostEqual(self.cart.total(), 28.5)

    def test_add_same_item_increases_quantity(self):
        self.cart.add_item("Pizza", 10.0, quantity=1)
        self.cart.add_item("Pizza", 10.0, quantity=2)
        self.assertEqual(self.cart.items["Pizza"].quantity, 3)

    def test_validate_order_empty_cart(self):
        result = self.order.validate_order()
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Cart is empty")

    def test_validate_order_with_unavailable_item(self):
        self.cart.add_item("Salad", 5.0, quantity=1)
        result = self.order.validate_order()
        self.assertFalse(result["success"])
        self.assertIn("Salad is not available", result["message"])

    def test_validate_order_success(self):
        self.cart.add_item("Pizza", 10.0, quantity=1)
        result = self.order.validate_order()
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Order is valid")


class PaymentProcessingTests(unittest.TestCase):
    def setUp(self):
        self.payment_method = PaymentMethod()
        self.processor = PaymentProcessing(self.payment_method)

    def test_validate_payment_method_supported(self):
        self.assertTrue(self.processor.validate_payment_method("credit_card"))

    def test_validate_payment_method_invalid(self):
        with self.assertRaises(ValueError):
            self.processor.validate_payment_method("bitcoin")

    def test_validate_credit_card_valid(self):
        self.assertTrue(self.processor.validate_credit_card("4242424242424242", "123"))

    def test_validate_credit_card_invalid_number(self):
        self.assertFalse(self.processor.validate_credit_card("123", "123"))

    def test_process_payment_success(self):
        # mock underlying method to force success
        self.payment_method.process_payment = MagicMock(return_value=True)
        message = self.processor.process_payment(10.0, "credit_card", "4242424242424242", "123")
        self.assertEqual(message, "Payment successful, Order confirmed")

    def test_process_payment_failure_from_gateway(self):
        self.payment_method.process_payment = MagicMock(return_value=False)
        message = self.processor.process_payment(10.0, "credit_card", "4242424242424242", "123")
        self.assertEqual(message, "Payment failed, please try again")

    def test_process_payment_invalid_method(self):
        message = self.processor.process_payment(10.0, "cash", "4242424242424242", "123")
        self.assertTrue(message.startswith("Error: Invalid payment method"))


class OrderHistoryTests(unittest.TestCase):
    def setUp(self):
        self.history = OrderHistory()

    def test_add_and_view_order_history(self):
        self.history.add_order("Order001", "Pizza", 25.0, "Delivered", "2023-09-15")
        orders = self.history.view_order_history()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["order_id"], "Order001")

    def test_filter_by_status(self):
        self.history.add_order("Order001", "Pizza", 25.0, "Delivered", "2023-09-15")
        self.history.add_order("Order002", "Sushi", 20.0, "Pending", "2023-09-16")
        delivered = self.history.filter_orders(status="Delivered")
        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0]["order_id"], "Order001")

    def test_filter_by_date(self):
        self.history.add_order("Order001", "Pizza", 25.0, "Delivered", "2023-09-15")
        self.history.add_order("Order002", "Sushi", 20.0, "Pending", "2023-09-16")
        d16 = self.history.filter_orders(date="2023-09-16")
        self.assertEqual(len(d16), 1)
        self.assertEqual(d16[0]["order_id"], "Order002")


if __name__ == "__main__":
    unittest.main()
