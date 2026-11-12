import os
import sqlite3
from contextlib import closing
from pathlib import Path


DATABASE_PATH = Path(
    os.environ.get(
        "DATABASE_PATH",
        str(Path(__file__).resolve().with_name("ecommerce.db")),
    )
).expanduser()

PRODUCTS = [
    (1, "Laptop", 50000),
    (2, "Mobile", 20000),
    (3, "Keyboard", 1000),
    (4, "Mouse", 500),
    (5, "Headphones", 2000),
    (6, "Smartwatch", 8000),
    (7, "Camera", 35000),
    (8, "Speaker", 4500),
    (9, "Tablet", 28000),
    (10, "Backpack", 3000),
]
DEMO_ORDERS = [
    ("u1", "Laptop", 1, 50000),
    ("u1", "Mouse", 1, 500),
    ("u2", "Laptop", 1, 50000),
    ("u2", "Keyboard", 1, 1000),
    ("u3", "Mobile", 1, 20000),
    ("u3", "Headphones", 1, 2000),
    ("u4", "Mobile", 1, 20000),
    ("u4", "Keyboard", 1, 1000),
    ("u5", "Headphones", 1, 2000),
    ("u5", "Mouse", 1, 500),
]
ADDITIONAL_DEMO_ORDERS = [
    ("u1", "Camera", 1, 35000),
    ("u1", "Backpack", 1, 3000),
    ("u2", "Smartwatch", 1, 8000),
    ("u2", "Camera", 1, 35000),
    ("u3", "Speaker", 1, 4500),
    ("u3", "Tablet", 1, 28000),
    ("u4", "Tablet", 1, 28000),
    ("u4", "Smartwatch", 1, 8000),
    ("u5", "Speaker", 1, 4500),
    ("u5", "Backpack", 1, 3000),
]


def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    price INTEGER NOT NULL CHECK(price >= 0)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    product TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    total INTEGER NOT NULL
                )
                """
            )
            connection.executemany(
                "INSERT OR IGNORE INTO products (id, name, price) VALUES (?, ?, ?)",
                PRODUCTS,
            )
            order_count = connection.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()[0]
            if order_count == 0:
                connection.executemany(
                    """
                    INSERT INTO orders (username, product, quantity, total)
                    VALUES (?, ?, ?, ?)
                    """,
                    DEMO_ORDERS,
                )
            connection.executemany(
                """
                INSERT INTO orders (username, product, quantity, total)
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM orders WHERE username = ? AND product = ?
                )
                """,
                [
                    (*order, order[0], order[1])
                    for order in ADDITIONAL_DEMO_ORDERS
                ],
            )
