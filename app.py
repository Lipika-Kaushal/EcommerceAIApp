import os
import secrets
import sqlite3
from contextlib import closing

from flask import Flask, flash, redirect, render_template, request, session, url_for

from database import DATABASE_PATH, initialize_database
from recommender import get_recommendations


initialize_database()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def get_products():
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        return connection.execute(
            "SELECT id, name, price FROM products ORDER BY id"
        ).fetchall()


def get_cart_items():
    cart = session.get("cart", {})
    products = {product[0]: product for product in get_products()}
    items = []
    for product_id, quantity in cart.items():
        try:
            product = products.get(int(product_id))
        except (TypeError, ValueError):
            product = None
        if product is not None and isinstance(quantity, int) and quantity > 0:
            items.append(
                {
                    "id": product[0],
                    "name": product[1],
                    "price": product[2],
                    "quantity": quantity,
                    "subtotal": product[2] * quantity,
                }
            )
    return items


@app.context_processor
def inject_cart_count():
    return {"cart_count": sum(item["quantity"] for item in get_cart_items())}


@app.template_filter("inr")
def format_inr(amount):
    return f"₹{amount:,.0f}"


@app.get("/")
@app.get("/shop")
def shop():
    return render_template("shop.html", products=get_products())


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

    product = next((p for p in get_products() if p[0] == product_id), None)
    if product is None or quantity < 1 or quantity > 99:
        flash("Choose a valid product and a quantity from 1 to 99.", "error")
        return redirect(destination)

    cart = session.get("cart", {})
    key = str(product_id)
    cart[key] = min(cart.get(key, 0) + quantity, 99)
    session["cart"] = cart
    flash(f"{product[1]} added to your bag.", "success")
    return redirect(destination)


@app.get("/cart")
def cart():
    items = get_cart_items()
    total = sum(item["subtotal"] for item in items)
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", {})
    if cart.pop(str(product_id), None) is None:
        flash("That item was not in your bag.", "error")
    else:
        session["cart"] = cart
        flash("Item removed from your bag.", "success")
    return redirect(url_for("cart"))


@app.get("/recommendations")
def recommendations():
    cart_items = get_cart_items()
    interests = [item["name"] for item in cart_items]
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        items = get_recommendations(connection, interests)
    return render_template(
        "recommendations.html",
        recommendations=items,
        cart_items=cart_items,
    )


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
