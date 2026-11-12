from flask import Flask, jsonify

from catalog_data import PRODUCTS
from microservices.common import (
    configure_api,
    database_path,
    open_database,
    rows_as_dicts,
)


app = Flask("catalog")
configure_api(app)
DB_PATH = database_path("catalog")

with open_database(DB_PATH) as connection:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            price INTEGER NOT NULL CHECK(price >= 0)
        )
        """
    )
    connection.executemany(
        "INSERT OR IGNORE INTO products (id, name, price) VALUES (?, ?, ?)",
        [(product["id"], product["name"], product["price"]) for product in PRODUCTS],
    )


@app.get("/api/products")
def list_products():
    with open_database(DB_PATH) as connection:
        products = rows_as_dicts(
            connection.execute("SELECT id, name, price FROM products ORDER BY id")
        )
    return jsonify(products)


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    with open_database(DB_PATH) as connection:
        product = connection.execute(
            "SELECT id, name, price FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    if product is None:
        return jsonify(error="Product not found."), 404
    return jsonify(dict(product))
