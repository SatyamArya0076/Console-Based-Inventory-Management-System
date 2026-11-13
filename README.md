# Inventory Manager

A beginner-friendly console application for managing products, stock, sales, and reports. It uses only Python's standard library and SQLite, so no package installation is needed.

## Requirements

- Python 3.8 or newer

## Run

From this folder, start the interactive menu:

```powershell
python inventory_manager.py
```

The app creates `inventory.db` beside the program on first run. Keep that file to preserve your products and sales between runs.

## Menu

- List, add, and update products
- Adjust stock (positive to add, negative to remove)
- Record a sale, which checks and reduces available stock
- View inventory totals, low-stock count, revenue, and recent sales

Each product has a unique SKU, name, unit price, current stock, and low-stock threshold. A sale stores the price at the time of sale, so later product price changes do not rewrite past sales.

## Run tests

```powershell
python -m unittest -v
```
