import json
import sqlite3
import uuid

from flask import Flask, jsonify

from catalog_data import SAMPLE_PURCHASES
from microservices.common import (
    ServiceError,
    api_request,
    configure_api,
    database_path,
    open_database,
    require_json_object,
    rows_as_dicts,
)


app = Flask("orders")
configure_api(app)
DB_PATH = database_path("orders")
CATALOG_URL = "http://catalog:8000"
CART_URL = "http://cart:8000"
INVENTORY_URL = "http://inventory:8000"

with open_database(DB_PATH) as connection:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            cart_id TEXT NOT NULL UNIQUE,
            total INTEGER NOT NULL,
            items_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            order_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            PRIMARY KEY(order_id, product_id)
        );
        CREATE TABLE IF NOT EXISTS sample_purchases (
            customer_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            PRIMARY KEY(customer_id, product_id)
        );
        """
    )
    existing = connection.execute(
        "SELECT COUNT(*) FROM sample_purchases"
    ).fetchone()[0]
    if not existing:
        connection.executemany(
            "INSERT INTO sample_purchases (customer_id, product_id) VALUES (?, ?)",
            [
                (customer, product_id)
                for customer, product_ids in SAMPLE_PURCHASES.items()
                for product_id in product_ids
            ],
        )


def get_history():
    with open_database(DB_PATH) as connection:
        samples = rows_as_dicts(
            connection.execute(
                "SELECT customer_id, product_id FROM sample_purchases"
            )
        )
        placed = rows_as_dicts(
            connection.execute(
                """
                SELECT orders.id AS customer_id, order_items.product_id
                FROM order_items
                JOIN orders ON orders.id = order_items.order_id
                """
            )
        )
    return samples + placed


@app.get("/api/orders/history")
def order_history():
    return jsonify(get_history())


@app.post("/api/orders")
def create_order():
    payload = require_json_object()
    cart_id = payload.get("cart_id")
    if not isinstance(cart_id, str) or not cart_id:
        raise ServiceError("Cart ID is required.", 400)

    existing = None
    with open_database(DB_PATH) as connection:
        existing = connection.execute(
            "SELECT id, total, items_json FROM orders WHERE cart_id = ?", (cart_id,)
        ).fetchone()
    if existing is not None:
        api_request(CART_URL, f"/api/carts/{cart_id}", method="DELETE")
        return jsonify(
            id=existing["id"],
            total=existing["total"],
            items=json.loads(existing["items_json"]),
        )

    cart = api_request(CART_URL, f"/api/carts/{cart_id}")
    cart_items = cart["items"]
    if not cart_items:
        raise ServiceError("Your bag is empty.", 400)

    products = api_request(CATALOG_URL, "/api/products")
    product_by_id = {product["id"]: product for product in products}
    order_items = []
    for item in cart_items:
        product = product_by_id.get(item["product_id"])
        if product is None:
            raise ServiceError(f"Product {item['product_id']} no longer exists.", 409)
        order_items.append(
            {
                "product_id": product["id"],
                "name": product["name"],
                "quantity": item["quantity"],
                "price": product["price"],
                "subtotal": product["price"] * item["quantity"],
            }
        )
    total = sum(item["subtotal"] for item in order_items)
    order_id = uuid.uuid4().hex

    api_request(
        INVENTORY_URL,
        "/api/inventory/reserve",
        method="POST",
        payload={"order_id": order_id, "items": order_items},
    )
    try:
        with open_database(DB_PATH) as connection:
            with connection:
                connection.execute(
                    "INSERT INTO orders (id, cart_id, total, items_json) VALUES (?, ?, ?, ?)",
                    (order_id, cart_id, total, json.dumps(order_items)),
                )
                connection.executemany(
                    "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
                    [
                        (order_id, item["product_id"], item["quantity"])
                        for item in order_items
                    ],
                )
    except sqlite3.Error:
        api_request(
            INVENTORY_URL,
            f"/api/inventory/release/{order_id}",
            method="POST",
        )
        raise

    api_request(CART_URL, f"/api/carts/{cart_id}", method="DELETE")
    return jsonify(id=order_id, total=total, items=order_items), 201


@app.get("/api/orders/<order_id>")
def get_order(order_id):
    with open_database(DB_PATH) as connection:
        order = connection.execute(
            "SELECT id, total, items_json, created_at FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
    if order is None:
        return jsonify(error="Order not found."), 404
    return jsonify(
        id=order["id"],
        total=order["total"],
        items=json.loads(order["items_json"]),
        created_at=order["created_at"],
    )
