from flask import Flask, jsonify

from microservices.common import api_request, configure_api, require_json_object
from recommender import build_recommendations


app = Flask("recommendations")
configure_api(app)
CATALOG_URL = "http://catalog:8000"
ORDERS_URL = "http://orders:8000"


@app.post("/api/recommendations")
def recommend():
    payload = require_json_object()
    cart_items = payload.get("items", [])
    if not isinstance(cart_items, list):
        return jsonify(error="Items must be a list."), 400
    product_ids = []
    for item in cart_items:
        if not isinstance(item, dict) or not isinstance(item.get("product_id"), int):
            return jsonify(error="Each cart item must have a product ID."), 400
        product_ids.append(item["product_id"])

    products = api_request(CATALOG_URL, "/api/products")
    history = api_request(ORDERS_URL, "/api/orders/history")
    recommendations = build_recommendations(products, product_ids, history)
    return jsonify(recommendations)
