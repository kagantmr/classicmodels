from flask import render_template, request, redirect, url_for, flash, session
import random
import string

db = None


def init_cart_routes(app, database):
    """Initialize cart-related routes."""
    global db
    db = database

    @app.route("/cart/add/<product_code>", methods=["POST"])
    def add_to_cart(product_code):
        if session.get("user_type") != "customer":
            flash("You need to be logged in as a customer to add items to cart.", "warning")
            return redirect(url_for("login"))

        product = db.get_single_product(product_code)
        if not product:
            flash("Product not found.", "danger")
            return redirect(url_for("index"))

        try:
            quantity = int(request.form.get("quantity", 1))
        except ValueError:
            quantity = 1

        if quantity <= 0:
            flash("Quantity must be at least 1.", "warning")
            return redirect(url_for("product_page", product_code=product_code))

        if "quantityInStock" in product and quantity > product["quantityInStock"]:
            flash("Not enough stock for this quantity.", "warning")
            return redirect(url_for("product_page", product_code=product_code))

        cart = get_cart()

        if product_code in cart:
            cart[product_code]["quantity"] += quantity
        else:
            cart[product_code] = {
                "productCode": product["productCode"],
                "productName": product["productName"],
                "priceEach": product.get("MSRP") or product.get("buyPrice") or 0,
                "quantity": quantity,
            }

        session["cart"] = cart

        flash(f"Added {quantity} x {product['productName']} to your cart.", "success")
        return redirect(url_for("product_page", product_code=product_code))

    @app.route("/cart/remove/<product_code>", methods=["POST"])
    def remove_from_cart(product_code):
        if session.get("user_type") != "customer":
            flash("You must be logged in as a customer.", "warning")
            return redirect(url_for("login"))

        cart = session.get("cart", {})
        if product_code in cart:
            del cart[product_code]
            session["cart"] = cart
            flash("Item removed.", "info")

        return redirect(url_for("view_cart"))

    @app.route("/cart/update/<product_code>", methods=["POST"])
    def update_cart(product_code):
        if session.get("user_type") != "customer":
            flash("You must be logged in as a customer.", "warning")
            return redirect(url_for("login"))

        cart = session.get("cart", {})
        if product_code not in cart:
            flash("Item not found in cart.", "danger")
            return redirect(url_for("view_cart"))

        try:
            qty = int(request.form.get("quantity", 1))
        except:
            qty = 1

        if qty < 1:
            qty = 1

        cart[product_code]["quantity"] = qty
        session["cart"] = cart
        return redirect(url_for("view_cart"))

    @app.route("/cart")
    def view_cart():
        user_type = session.get("user_type")

        if user_type == "employee":
            return redirect(url_for("index"))

        if user_type != "customer":
            flash("You need to be logged in as a customer to view your cart.", "warning")
            return redirect(url_for("login"))

        cart = session.get("cart", {})
        total = sum(item["priceEach"] * item["quantity"] for item in cart.values())

        return render_template("cart.html", cart=cart, total=total)

    @app.route("/checkout", methods=["GET"])
    def checkout():
        if session.get("user_type") != "customer":
            flash("You must be logged in as a customer to checkout.", "warning")
            return redirect(url_for("login"))

        cart = session.get("cart", {})
        if not cart:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("view_cart"))

        total = sum(item["priceEach"] * item["quantity"] for item in cart.values())

        return render_template("checkout.html", cart=cart, total=total)

    @app.route("/place_order", methods=["POST"])
    def place_order():
        if session.get("user_type") != "customer":
            flash("You must be logged in as a customer.", "warning")
            return redirect(url_for("login"))

        cart = session.get("cart", {})
        if not cart:
            flash("Cart is empty.", "warning")
            return redirect(url_for("view_cart"))

        customerNumber = session.get("user_number")

        total_amount = sum(item["priceEach"] * item["quantity"] for item in cart.values())

        result = db.execute_query("SELECT MAX(orderNumber) AS maxNum FROM orders")
        next_order_number = (result[0]["maxNum"] or 0) + 1

        db.execute_query(
            """
            INSERT INTO orders (orderNumber, orderDate, requiredDate, shippedDate, status, comments, customerNumber)
            VALUES (%s, NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY), NULL, 'In Process', %s, %s)
            """,
            (next_order_number, "Web order", customerNumber)
        )

        line_number = 1
        for product_code, item in cart.items():
            quantity = item["quantity"]
            price_each = item["priceEach"]
            db.execute_query(
                """
                INSERT INTO orderdetails (orderNumber, productCode, quantityOrdered, priceEach, orderLineNumber)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (next_order_number, product_code, quantity, price_each, line_number)
            )
            line_number += 1

        session["cart"] = {}

        flash(f"Order #{next_order_number} placed successfully!", "success")
        return redirect(url_for("order_detail", order_number=next_order_number))

def get_cart():
    """Return the current cart stored in session."""
    if "cart" not in session:
        session["cart"] = {}
    return session["cart"]

