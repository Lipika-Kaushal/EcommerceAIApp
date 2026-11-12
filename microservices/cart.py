from flask import Flask, jsonify

from microservices.common import (
    ServiceError,
    api_request,
    configure_api,
    database_path,
    open_database,
    require_json_object,
    rows_as_dicts,
)


app = Flask("cart")
configure_api(app)
DB_PATH = database_path("cart")
CATALOG_URL = "http://catalog:8000"

with open_database(DB_PATH) as connection:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cart_items (
            cart_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 99),
            PRIMARY KEY(cart_id, product_id)
        )
        """
    )


def valid_cart_id(cart_id):
    return bool(cart_id) and len(cart_id) <= 80 and all(
        character.isalnum() or character in "-_" for character in cart_id
    )


def check_product(product_id):
    api_request(CATALOG_URL, f"/api/products/{product_id}")


@app.get("/api/carts/<cart_id>")
def get_cart(cart_id):
    if not valid_cart_id(cart_id):
        raise ServiceError("Invalid cart ID.", 400)
    with open_database(DB_PATH) as connection:
        items = rows_as_dicts(
            connection.execute(
                "SELECT product_id, quantity FROM cart_items WHERE cart_id = ? ORDER BY product_id",
                (cart_id,),
            )
        )
    return jsonify(cart_id=cart_id, items=items)


@app.post("/api/carts/<cart_id>/items")
def add_item(cart_id):
    if not valid_cart_id(cart_id):
        raise ServiceError("Invalid cart ID.", 400)
    payload = require_json_object()
    product_id = payload.get("product_id")
    quantity = payload.get("quantity", 1)
    if not isinstance(product_id, int) or not isinstance(quantity, int):
        raise ServiceError("Product ID and quantity must be integers.", 400)
    if not 1 <= quantity <= 99:
        raise ServiceError("Quantity must be between 1 and 99.", 400)
    check_product(product_id)

    with open_database(DB_PATH) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO cart_items (cart_id, product_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(cart_id, product_id)
                DO UPDATE SET quantity = CASE
                    WHEN cart_items.quantity + excluded.quantity > 99 THEN 99
                    ELSE cart_items.quantity + excluded.quantity
                END
                """,
                (cart_id, product_id, quantity),
            )
            item = connection.execute(
                "SELECT product_id, quantity FROM cart_items WHERE cart_id = ? AND product_id = ?",
                (cart_id, product_id),
            ).fetchone()
    return jsonify(dict(item)), 201


@app.delete("/api/carts/<cart_id>/items/<int:product_id>")
def remove_item(cart_id, product_id):
    if not valid_cart_id(cart_id):
        raise ServiceError("Invalid cart ID.", 400)
    with open_database(DB_PATH) as connection:
        with connection:
            connection.execute(
                "DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?",
                (cart_id, product_id),
            )
    return jsonify(status="removed")


@app.delete("/api/carts/<cart_id>")
def clear_cart(cart_id):
    if not valid_cart_id(cart_id):
        raise ServiceError("Invalid cart ID.", 400)
    with open_database(DB_PATH) as connection:
        with connection:
            connection.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
    return jsonify(status="cleared")
