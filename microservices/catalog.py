import os

from flask import Flask, jsonify
from pymongo import MongoClient

from catalog_data import PRODUCTS
from microservices.common import configure_api


app = Flask("catalog")
configure_api(app)
mongo_client = MongoClient(
    host=os.environ.get("MONGO_HOST", "localhost"),
    port=int(os.environ.get("MONGO_PORT", "27017")),
    username=os.environ.get("MONGO_USER") or None,
    password=os.environ.get("MONGO_PASSWORD") or None,
    authSource="admin",
    serverSelectionTimeoutMS=5000,
)
mongo_client.admin.command("ping")
products_collection = mongo_client.goodfind_catalog.products
products_collection.create_index("id", unique=True)
for product in PRODUCTS:
    products_collection.update_one(
        {"id": product["id"]},
        {"$setOnInsert": product},
        upsert=True,
    )


@app.get("/api/products")
def list_products():
    products = list(products_collection.find({}, {"_id": 0}).sort("id", 1))
    return jsonify(products)


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    product = products_collection.find_one({"id": product_id}, {"_id": 0})
    if product is None:
        return jsonify(error="Product not found."), 404
    return jsonify(product)
