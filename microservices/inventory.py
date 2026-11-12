import sqlite3

from flask import Flask, jsonify

from catalog_data import PRODUCTS
from microservices.common import (
    ServiceError,
    configure_api,
    database_path,
    open_database,
    require_json_object,
    rows_as_dicts,
)


app = Flask("inventory")
configure_api(app)
DB_PATH = database_path("inventory")

with open_database(DB_PATH) as connection:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            product_id INTEGER PRIMARY KEY,
            available INTEGER NOT NULL CHECK(available >= 0)
        );
        CREATE TABLE IF NOT EXISTS reservations (
            order_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            PRIMARY KEY(order_id, product_id)
        );
        """
    )
    connection.executemany(
        "INSERT OR IGNORE INTO inventory (product_id, available) VALUES (?, 25)",
        [(product["id"],) for product in PRODUCTS],
    )


@app.get("/api/inventory")
def list_inventory():
    with open_database(DB_PATH) as connection:
        items = rows_as_dicts(
            connection.execute(
                "SELECT product_id, available FROM inventory ORDER BY product_id"
            )
        )
    return jsonify(items)


@app.post("/api/inventory/reserve")
def reserve_inventory():
    payload = require_json_object()
    order_id = payload.get("order_id")
    items = payload.get("items")
    if not isinstance(order_id, str) or not order_id or not isinstance(items, list):
        raise ServiceError("Order ID and items are required.", 400)

    normalized = {}
    for item in items:
        if not isinstance(item, dict):
            raise ServiceError("Each item must be an object.", 400)
        product_id = item.get("product_id")
        quantity = item.get("quantity")
        if (
            not isinstance(product_id, int)
            or not isinstance(quantity, int)
            or quantity < 1
        ):
            raise ServiceError("Product IDs and positive quantities are required.", 400)
        normalized[product_id] = normalized.get(product_id, 0) + quantity

    with open_database(DB_PATH) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT product_id FROM reservations WHERE order_id = ?",
                (order_id,),
            ).fetchall()
            if existing:
                connection.rollback()
                raise ServiceError("Inventory is already reserved for this order.", 409)

            for product_id, quantity in normalized.items():
                updated = connection.execute(
                    """
                    UPDATE inventory
                    SET available = available - ?
                    WHERE product_id = ? AND available >= ?
                    """,
                    (quantity, product_id, quantity),
                )
                if updated.rowcount != 1:
                    exists = connection.execute(
                        "SELECT 1 FROM inventory WHERE product_id = ?", (product_id,)
                    ).fetchone()
                    connection.rollback()
                    if exists is None:
                        raise ServiceError(f"Inventory not found for product {product_id}.", 404)
                    raise ServiceError(f"Not enough stock for product {product_id}.", 409)
                connection.execute(
                    """
                    INSERT INTO reservations (order_id, product_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (order_id, product_id, quantity),
                )
            connection.commit()
        except ServiceError:
            raise
        except sqlite3.Error:
            connection.rollback()
            raise

    return jsonify(order_id=order_id, status="reserved")


@app.post("/api/inventory/release/<order_id>")
def release_inventory(order_id):
    with open_database(DB_PATH) as connection:
        with connection:
            reservations = connection.execute(
                "SELECT product_id, quantity FROM reservations WHERE order_id = ?",
                (order_id,),
            ).fetchall()
            for reservation in reservations:
                connection.execute(
                    "UPDATE inventory SET available = available + ? WHERE product_id = ?",
                    (reservation["quantity"], reservation["product_id"]),
                )
            connection.execute("DELETE FROM reservations WHERE order_id = ?", (order_id,))
    return jsonify(order_id=order_id, status="released")
