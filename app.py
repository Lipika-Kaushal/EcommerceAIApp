import os
import secrets
import uuid

from flask import Flask, flash, redirect, render_template, request, session, url_for

from microservices.common import ServiceError, api_request


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

SERVICE_URLS = {
    "catalog": os.environ.get("CATALOG_URL", "http://localhost:8101"),
    "cart": os.environ.get("CART_URL", "http://localhost:8102"),
    "recommendations": os.environ.get(
        "RECOMMENDATIONS_URL", "http://localhost:8103"
    ),
    "orders": os.environ.get("ORDERS_URL", "http://localhost:8104"),
}


def service_call(service, path, method="GET", payload=None):
    return api_request(SERVICE_URLS[service], path, method, payload)


def current_cart_id():
    if "cart_id" not in session:
        session["cart_id"] = uuid.uuid4().hex
    return session["cart_id"]


def get_cart_items():
    cart = service_call("cart", f"/api/carts/{current_cart_id()}")
    products = service_call("catalog", "/api/products")
    product_by_id = {product["id"]: product for product in products}
    items = []
    for item in cart["items"]:
        product = product_by_id.get(item["product_id"])
        if product is None:
            raise ServiceError(
                f"Product {item['product_id']} in the cart is missing from the catalog.",
                502,
            )
        items.append(
            {
                **product,
                "quantity": item["quantity"],
                "subtotal": product["price"] * item["quantity"],
            }
        )
    return items


@app.template_filter("inr")
def format_inr(amount):
    return f"₹{amount:,.0f}"


@app.errorhandler(ServiceError)
def handle_service_error(error):
    status_code = error.status_code if 400 <= error.status_code < 500 else 503
    return render_template("service_error.html", message=error.message), status_code


@app.get("/health")
def health():
    return {"status": "ok", "service": "storefront"}


@app.get("/")
@app.get("/shop")
def shop():
    products = service_call("catalog", "/api/products")
    cart_count = sum(item["quantity"] for item in get_cart_items())
    return render_template("shop.html", products=products, cart_count=cart_count)


@app.post("/cart/add")
def add_to_cart():
    return_to = request.form.get("return_to")
    destination = (
        url_for(return_to)
        if return_to in {"shop", "cart", "recommendations"}
        else url_for("shop")
    )
    try:
        product_id = int(request.form.get("product_id", ""))
        quantity = int(request.form.get("quantity", "1"))
    except ValueError:
        flash("Choose a valid product and quantity.", "error")
        return redirect(destination)

    service_call(
        "cart",
        f"/api/carts/{current_cart_id()}/items",
        "POST",
        {"product_id": product_id, "quantity": quantity},
    )
    flash("Added to your bag.", "success")
    return redirect(destination)


@app.get("/cart")
def cart():
    items = get_cart_items()
    total = sum(item["subtotal"] for item in items)
    cart_count = sum(item["quantity"] for item in items)
    return render_template(
        "cart.html", items=items, total=total, cart_count=cart_count
    )


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    service_call(
        "cart",
        f"/api/carts/{current_cart_id()}/items/{product_id}",
        "DELETE",
    )
    flash("Item removed from your bag.", "success")
    return redirect(url_for("cart"))


@app.get("/recommendations")
def recommendations():
    cart_items = get_cart_items()
    result = service_call(
        "recommendations",
        "/api/recommendations",
        "POST",
        {"items": [{"product_id": item["id"]} for item in cart_items]},
    )
    return render_template(
        "recommendations.html",
        recommendations=result,
        cart_items=cart_items,
        cart_count=sum(item["quantity"] for item in cart_items),
    )


@app.post("/checkout")
def checkout():
    order = service_call(
        "orders",
        "/api/orders",
        "POST",
        {"cart_id": current_cart_id()},
    )
    session["cart_id"] = uuid.uuid4().hex
    return render_template("confirmation.html", order=order, cart_count=0)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
