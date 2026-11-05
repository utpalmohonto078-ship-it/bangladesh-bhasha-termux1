import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sales_manager import (
    add_customer, set_price, create_order, list_customers,
    list_orders, sales_report,
)


class SalesManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "sales-test.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_customer_registration(self):
        cid = add_customer("buyer@example.com", "Test Buyer", db_path=self.db)
        self.assertGreater(cid, 0)
        self.assertEqual(len(list_customers(self.db)), 1)

    def test_duplicate_customer_updates(self):
        add_customer("buyer@example.com", "First", db_path=self.db)
        add_customer("buyer@example.com", "Updated", db_path=self.db)
        rows = list_customers(self.db)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "Updated")

    def test_price_and_order(self):
        add_customer("buyer@example.com", "Test Buyer", db_path=self.db)
        set_price("Professional", "1250", "BDT", self.db)
        order = create_order("buyer@example.com", "Professional", self.db)
        self.assertTrue(order["invoice_no"].startswith("BBH-"))
        self.assertEqual(order["status"], "unpaid")
        self.assertEqual(len(list_orders(self.db)), 1)

    def test_order_requires_price(self):
        add_customer("buyer@example.com", "Test Buyer", db_path=self.db)
        with self.assertRaises(ValueError):
            create_order("buyer@example.com", "Enterprise", self.db)

    def test_invalid_customer_rejected(self):
        with self.assertRaises(ValueError):
            add_customer("not-an-email", "Test Buyer", db_path=self.db)


if __name__ == "__main__":
    unittest.main()
