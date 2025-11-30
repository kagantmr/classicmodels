from flask import render_template, redirect, url_for, flash, session, request

db = None


def init_main_routes(app, database):
    """Initialize main/public routes."""
    global db
    db = database

    @app.route('/')
    def index():
        offices = db.get_all_offices()
        return render_template('index.html', offices=offices)

    @app.route('/productlines')
    def productlines():
        productlines_data = db.execute_query(("SELECT productLine, textDescription FROM productlines"))
        return render_template('productlines.html', productlines=productlines_data)

    @app.route("/products/<product_line>")
    def products_by_line(product_line):
        sort = request.args.get("sort")

        if not sort or sort == "price_asc" or sort == "price_desc":
            query = "SELECT * FROM products WHERE productLine = %s"
            products = db.execute_query(query, (product_line,))
            
            if sort == "price_asc":
                products = sorted(products, key=lambda x: x["MSRP"])
            elif sort == "price_desc":
                products = sorted(products, key=lambda x: x["MSRP"], reverse=True)

        elif sort == "popular":
            products = db.sort_popular_products(product_line)

        return render_template("products.html", products=products, product_line=product_line,sort=sort)

    @app.route("/product/<product_code>")
    def product_page(product_code):
        product = db.get_single_product(product_code)
        if not product:
            return "Product not found", 404

        cart = get_cart()
        in_cart_qty = 0
        if product_code in cart:
            in_cart_qty = cart[product_code]["quantity"]

        return render_template("product.html", product=product, in_cart_qty=in_cart_qty)

    @app.route("/profile")
    def my_profile():
        if not session.get("user_number"):
            flash("You need to log in to view your profile.", "danger")
            return redirect(url_for("login"))

        user_type = session.get("user_type")

        if user_type == "employee":
            return redirect(url_for("employee_dashboard"))
        elif user_type == "customer":
            return redirect(url_for("customer_profile"))
        else:
            flash("Your profile type is unknown.", "danger")
            return redirect(url_for("index"))


def get_cart():
    """Return the current cart stored in session as a dict."""
    if "cart" not in session:
        session["cart"] = {}
    return session["cart"]
