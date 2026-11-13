# Inventory Management System

A console-based Inventory Management System developed using **Python and SQLite**. This project helps users manage products, maintain stock, record sales, and generate inventory and sales reports through a simple command-line interface.

## Features

- Add new products with unique SKUs.
- View all available products.
- Update product details, prices, and stock thresholds.
- Increase or decrease product stock.
- Record product sales.
- Automatically update stock after every sale.
- Prevent sales when stock is insufficient.
- Prevent negative stock quantities.
- Generate inventory reports.
- Generate sales reports.
- Display the 10 most recent sales.
- Store data permanently using SQLite.

## Technologies Used

- Python 3.8+
- SQLite Database
- Python `sqlite3` module
- Python `unittest` module

## Project Structure

```text
Inventory-Management-System/
│
├── inventory_manager.py
├── test_inventory_manager.py
├── inventory.db
└── README.md
```

## Installation and Setup

**Step 1: Install Python**

Install Python 3.8 or above.

Check Python installation:

```bash
python --version
```

**Step 2: Clone the Repository**

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
```

**Step 3: Open the Project Folder**

```bash
cd YOUR-REPOSITORY
```

**Step 4: Run the Application**

```bash
python inventory_manager.py
```

No additional Python packages are required.

## Application Menu

```text
=== Inventory Manager ===

1. List products
2. Add product
3. Update product
4. Adjust stock
5. Record sale
6. View reports
0. Exit

Choose an option:
```

## Database Information

The project uses SQLite with two main tables:

| Table Name | Description |
|---|---|
| products | Stores product information, SKU, price, stock, and low-stock threshold. |
| sales | Stores sales transactions, quantities, prices, totals, and timestamps. |

The database file `inventory.db` is automatically created when the application runs for the first time.

## Reports

**Inventory Report**
- Total number of products
- Total units available
- Total inventory value
- Low-stock product count

**Sales Report**
- Total sales transactions
- Total units sold
- Total sales revenue
- Recent sales history

## Run Unit Tests

Execute the following command:

```bash
python -m unittest -v
```

The tests cover sales recording, stock deduction, insufficient stock, duplicate SKUs, negative stock prevention, and invalid prices.

## Future Enhancements

- User authentication and login system.
- Product categories and supplier management.
- Export reports to CSV or Excel.
- Graphical User Interface (GUI).
- Advanced sales analytics.

## Author

**Satyam Arya**

Developed as a Python project to demonstrate inventory management, database operations, and object-oriented programming concepts.

If you like this project, don't forget to give the repository a ⭐ on GitHub!
