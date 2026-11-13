import tempfile
import unittest
from pathlib import Path

from inventory_manager import InventoryManager


class InventoryManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test_inventory.db"
        self.manager = InventoryManager(database_path)

    def tearDown(self):
        self.manager.close()
        self.temp_dir.cleanup()

    def test_sale_reduces_stock_and_updates_sales_report(self):
        self.manager.add_product("abc-1", "Notebook", 2.50, 8)

        total = self.manager.record_sale("ABC-1", 3)

        self.assertEqual(total, 7.5)
        self.assertEqual(self.manager.list_products()[0]["stock"], 5)
        summary, sales = self.manager.sales_report()
        self.assertEqual(summary["sale_count"], 1)
        self.assertEqual(summary["units_sold"], 3)
        self.assertEqual(summary["revenue"], 7.5)
        self.assertEqual(sales[0]["sku"], "ABC-1")

    def test_failed_sale_does_not_change_stock_or_create_sale(self):
        self.manager.add_product("ABC-1", "Notebook", 2.50, 2)

        with self.assertRaisesRegex(ValueError, "Not enough stock"):
            self.manager.record_sale("ABC-1", 3)

        self.assertEqual(self.manager.list_products()[0]["stock"], 2)
        self.assertEqual(self.manager.sales_report()[0]["sale_count"], 0)

    def test_stock_cannot_be_adjusted_below_zero(self):
        self.manager.add_product("ABC-1", "Notebook", 2.50, 2)

        with self.assertRaisesRegex(ValueError, "below zero"):
            self.manager.adjust_stock("ABC-1", -3)

        self.assertEqual(self.manager.list_products()[0]["stock"], 2)

    def test_duplicate_sku_is_rejected_case_insensitively(self):
        self.manager.add_product("abc-1", "Notebook", 2.50, 2)

        with self.assertRaisesRegex(ValueError, "already exists"):
            self.manager.add_product("ABC-1", "Other notebook", 3.00, 1)

    def test_non_finite_price_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            self.manager.add_product("ABC-1", "Notebook", float("inf"), 2)


if __name__ == "__main__":
    unittest.main()
