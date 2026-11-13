"""Console-based inventory management application."""

import math
import sqlite3
from pathlib import Path


class InventoryManager:
    def __init__(self, database_path):
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize_database()

    def close(self):
        self.connection.close()

    def _initialize_database(self):
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    sku TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    price REAL NOT NULL CHECK (price >= 0),
                    stock INTEGER NOT NULL CHECK (stock >= 0),
                    low_stock_at INTEGER NOT NULL DEFAULT 5
                        CHECK (low_stock_at >= 0)
                )
                """
            )
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY,
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    unit_price REAL NOT NULL CHECK (unit_price >= 0),
                    total REAL NOT NULL CHECK (total >= 0),
                    sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self.connection.execute(
                "CREATE INDEX IF NOT EXISTS sales_sold_at_idx ON sales(sold_at)"
            )

    @staticmethod
    def _positive_integer(value, label, allow_zero=False):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("{} must be a whole number.".format(label))
        if value < 0 or (value == 0 and not allow_zero):
            qualifier = "zero or greater" if allow_zero else "greater than zero"
            raise ValueError("{} must be {}.".format(label, qualifier))
        return value

    @staticmethod
    def _price(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Price must be a number.")
        if not math.isfinite(value) or value < 0:
            raise ValueError("Price must be a finite, non-negative number.")
        return round(float(value), 2)

    def add_product(self, sku, name, price, stock, low_stock_at=5):
        sku = sku.strip().upper()
        name = name.strip()
        if not sku or not name:
            raise ValueError("SKU and product name are required.")
        price = self._price(price)
        stock = self._positive_integer(stock, "Stock", allow_zero=True)
        low_stock_at = self._positive_integer(
            low_stock_at, "Low-stock threshold", allow_zero=True
        )
        try:
            with self.connection:
                self.connection.execute(
                    """
                    INSERT INTO products (sku, name, price, stock, low_stock_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (sku, name, price, stock, low_stock_at),
                )
        except sqlite3.IntegrityError as error:
            if "products.sku" in str(error):
                raise ValueError("A product with that SKU already exists.") from error
            raise

    def list_products(self):
        return self.connection.execute(
            "SELECT sku, name, price, stock, low_stock_at "
            "FROM products ORDER BY name COLLATE NOCASE"
        ).fetchall()

    def update_product(self, sku, name=None, price=None, low_stock_at=None):
        sku = sku.strip().upper()
        updates = []
        values = []
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Product name cannot be empty.")
            updates.append("name = ?")
            values.append(name)
        if price is not None:
            updates.append("price = ?")
            values.append(self._price(price))
        if low_stock_at is not None:
            updates.append("low_stock_at = ?")
            values.append(
                self._positive_integer(
                    low_stock_at, "Low-stock threshold", allow_zero=True
                )
            )
        if not updates:
            raise ValueError("Enter at least one product field to update.")

        with self.connection:
            cursor = self.connection.execute(
                "UPDATE products SET {} WHERE sku = ?".format(", ".join(updates)),
                values + [sku],
            )
        if cursor.rowcount == 0:
            raise ValueError("No product found with SKU {}.".format(sku))

    def adjust_stock(self, sku, change):
        sku = sku.strip().upper()
        if isinstance(change, bool) or not isinstance(change, int) or change == 0:
            raise ValueError("Stock change must be a non-zero whole number.")
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE products SET stock = stock + ? "
                "WHERE sku = ? AND stock + ? >= 0",
                (change, sku, change),
            )
        if cursor.rowcount == 0:
            exists = self.connection.execute(
                "SELECT 1 FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            if exists:
                raise ValueError("Stock cannot be reduced below zero.")
            raise ValueError("No product found with SKU {}.".format(sku))

    def record_sale(self, sku, quantity):
        sku = sku.strip().upper()
        quantity = self._positive_integer(quantity, "Sale quantity")
        with self.connection:
            product = self.connection.execute(
                "SELECT id, price FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            if product is None:
                raise ValueError("No product found with SKU {}.".format(sku))
            cursor = self.connection.execute(
                "UPDATE products SET stock = stock - ? "
                "WHERE id = ? AND stock >= ?",
                (quantity, product["id"], quantity),
            )
            if cursor.rowcount == 0:
                raise ValueError("Not enough stock to complete this sale.")
            total = round(product["price"] * quantity, 2)
            self.connection.execute(
                """
                INSERT INTO sales (product_id, quantity, unit_price, total)
                VALUES (?, ?, ?, ?)
                """,
                (product["id"], quantity, product["price"], total),
            )
        return total

    def inventory_report(self):
        return self.connection.execute(
            """
            SELECT COUNT(*) AS product_count,
                   COALESCE(SUM(stock), 0) AS units_in_stock,
                   COALESCE(SUM(price * stock), 0) AS inventory_value,
                   COALESCE(SUM(CASE WHEN stock <= low_stock_at
                                     THEN 1 ELSE 0 END), 0) AS low_stock_count
            FROM products
            """
        ).fetchone()

    def sales_report(self):
        summary = self.connection.execute(
            """
            SELECT COUNT(*) AS sale_count,
                   COALESCE(SUM(quantity), 0) AS units_sold,
                   COALESCE(SUM(total), 0) AS revenue
            FROM sales
            """
        ).fetchone()
        recent_sales = self.connection.execute(
            """
            SELECT p.sku, p.name, s.quantity, s.unit_price, s.total, s.sold_at
            FROM sales AS s
            JOIN products AS p ON p.id = s.product_id
            ORDER BY s.id DESC
            LIMIT 10
            """
        ).fetchall()
        return summary, recent_sales


def _read_integer(prompt, minimum=None, default=None):
    entered = input(prompt).strip()
    value = default if not entered and default is not None else int(entered)
    if minimum is not None and value < minimum:
        raise ValueError("Enter a number no smaller than {}.".format(minimum))
    return value


def _read_price(prompt):
    value = float(input(prompt))
    if not math.isfinite(value) or value < 0:
        raise ValueError("Price must be a finite, non-negative number.")
    return value


def _show_products(manager):
    products = manager.list_products()
    if not products:
        print("No products have been added.")
        return
    print("\nSKU       PRODUCT                   PRICE      STOCK  LOW AT")
    print("-" * 66)
    for product in products:
        print(
            "{:<9} {:<25} {:>8.2f} {:>8} {:>7}".format(
                product["sku"],
                product["name"][:25],
                product["price"],
                product["stock"],
                product["low_stock_at"],
            )
        )


def _show_reports(manager):
    inventory = manager.inventory_report()
    summary, sales = manager.sales_report()
    print("\nInventory report")
    print("Products: {}".format(inventory["product_count"]))
    print("Units in stock: {}".format(inventory["units_in_stock"]))
    print("Inventory value: {:.2f}".format(inventory["inventory_value"]))
    print("Products at or below their low-stock threshold: {}".format(
        inventory["low_stock_count"]
    ))
    print("\nSales report")
    print("Transactions: {}".format(summary["sale_count"]))
    print("Units sold: {}".format(summary["units_sold"]))
    print("Total revenue: {:.2f}".format(summary["revenue"]))
    if sales:
        print("\nRecent sales")
        for sale in sales:
            print(
                "{} | {} ({}) x{} at {:.2f} = {:.2f}".format(
                    sale["sold_at"],
                    sale["name"],
                    sale["sku"],
                    sale["quantity"],
                    sale["unit_price"],
                    sale["total"],
                )
            )


def run(manager):
    actions = {
        "1": ("List products", lambda: _show_products(manager)),
        "2": ("Add product", lambda: _add_product(manager)),
        "3": ("Update product", lambda: _update_product(manager)),
        "4": ("Adjust stock", lambda: _adjust_stock(manager)),
        "5": ("Record sale", lambda: _record_sale(manager)),
        "6": ("View reports", lambda: _show_reports(manager)),
    }
    while True:
        print("\n=== Inventory Manager ===")
        for key, (label, _) in actions.items():
            print("{}. {}".format(key, label))
        print("0. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            return
        action = actions.get(choice)
        if action is None:
            print("Choose one of the listed options.")
            continue
        try:
            action[1]()
        except (ValueError, sqlite3.Error) as error:
            print("Error: {}".format(error))


def _add_product(manager):
    sku = input("SKU: ")
    name = input("Product name: ")
    price = _read_price("Unit price: ")
    stock = _read_integer("Starting stock: ", minimum=0)
    threshold = _read_integer("Low-stock threshold [5]: ", minimum=0, default=5)
    manager.add_product(sku, name, price, stock, threshold)
    print("Product added.")


def _update_product(manager):
    sku = input("SKU to update: ")
    name = input("New name (leave blank to keep current): ").strip()
    price_text = input("New price (leave blank to keep current): ").strip()
    threshold_text = input(
        "New low-stock threshold (leave blank to keep current): "
    ).strip()
    manager.update_product(
        sku,
        name=name or None,
        price=_read_price_from_text(price_text) if price_text else None,
        low_stock_at=int(threshold_text) if threshold_text else None,
    )
    print("Product updated.")


def _read_price_from_text(value):
    price = float(value)
    if not math.isfinite(price) or price < 0:
        raise ValueError("Price must be a finite, non-negative number.")
    return price


def _adjust_stock(manager):
    sku = input("SKU: ")
    change = _read_integer("Stock change (use a negative number to remove stock): ")
    manager.adjust_stock(sku, change)
    print("Stock updated.")


def _record_sale(manager):
    sku = input("SKU: ")
    quantity = _read_integer("Quantity sold: ", minimum=1)
    total = manager.record_sale(sku, quantity)
    print("Sale recorded. Total: {:.2f}".format(total))


def main():
    database_path = Path(__file__).with_name("inventory.db")
    manager = InventoryManager(database_path)
    try:
        run(manager)
    finally:
        manager.close()


if __name__ == "__main__":
    main()
