from flask import render_template, request, redirect, url_for, flash, session
import re

db = None


def init_product_routes(app, database):
    """Initialize product-related routes."""
    global db
    db = database

    # --- Helper: require employee role (you can adjust this logic) ---
    def _require_employee():
        if session.get("user_type") != "employee":
            flash("You must be an employee to manage products.", "danger")
            return False
        return True

    # --- List all products ---
    @app.route("/products")
    def products_list():
        if not _require_employee():
            return redirect(url_for("index"))

        products = db.execute_query(
            "SELECT * FROM products ORDER BY productLine, productName"
        )
        return render_template("products_list.html", products=products)

    # --- Create new product ---
    @app.route("/products/create", methods=["GET", "POST"])
    def create_product():
        if not _require_employee():
            return redirect(url_for("index"))

        if request.method == "POST":
            # Get form inputs
            productCode = request.form.get("productCode", "").strip()
            productName = request.form.get("productName", "").strip()
            productLine = request.form.get("productLine", "").strip()
            productScale = request.form.get("productScale", "").strip()
            productVendor = request.form.get("productVendor", "").strip()
            productDescription = request.form.get("productDescription", "").strip()
            quantityInStock_raw = request.form.get("quantityInStock", "").strip()
            buyPrice_raw = request.form.get("buyPrice", "").strip()
            msrp_raw = request.form.get("MSRP", "").strip()

            errors = []

            # --- Required field checks ---
            if not (productCode and productName and productLine and productScale and
                    productVendor and productDescription and quantityInStock_raw and
                    buyPrice_raw and msrp_raw):
                errors.append("All fields are required.")

            # --- Length checks based on table schema ---
            if len(productCode) > 15:
                errors.append("Product code cannot exceed 15 characters.")
            if len(productName) > 70:
                errors.append("Product name cannot exceed 70 characters.")
            if len(productLine) > 50:
                errors.append("Product line cannot exceed 50 characters.")
            if len(productScale) > 10:
                errors.append("Product scale cannot exceed 10 characters.")
            if len(productVendor) > 50:
                errors.append("Product vendor cannot exceed 50 characters.")

            # --- Numeric conversions & validation ---
            quantityInStock = None
            buyPrice = None
            msrp = None

            if quantityInStock_raw:
                try:
                    quantityInStock = int(quantityInStock_raw)
                    if quantityInStock < 0:
                        errors.append("Quantity in stock cannot be negative.")
                except ValueError:
                    errors.append("Quantity in stock must be an integer.")

            if buyPrice_raw:
                try:
                    buyPrice = float(buyPrice_raw)
                    if buyPrice <= 0:
                        errors.append("Buy price must be positive.")
                except ValueError:
                    errors.append("Buy price must be a valid number.")

            if msrp_raw:
                try:
                    msrp = float(msrp_raw)
                    if msrp <= 0:
                        errors.append("MSRP must be positive.")
                except ValueError:
                    errors.append("MSRP must be a valid number.")

            # --- Logical check: MSRP >= buyPrice ---
            if buyPrice is not None and msrp is not None and msrp < buyPrice:
                errors.append("MSRP should not be lower than buy price.")

            # --- Check productCode uniqueness ---
            if productCode:
                existing = db.execute_query(
                    "SELECT productCode FROM products WHERE productCode = %s",
                    (productCode,),
                    fetchone=True,
                )
                if existing:
                    errors.append("A product with this code already exists.")

            # --- Check productLine exists in productlines table ---
            if productLine:
                line = db.execute_query(
                    "SELECT productLine FROM productlines WHERE productLine = %s",
                    (productLine,),
                    fetchone=True,
                )
                if not line:
                    errors.append("Product line does not exist.")

            # If any errors, re-render form with old data
            if errors:
                return render_template(
                    "product_form.html",
                    errors=errors,
                    form=request.form,
                    mode="create",
                )

            # --- If everything is valid, insert product ---
            product_info = (
                productCode,
                productName,
                productLine,
                productScale,
                productVendor,
                productDescription,
                quantityInStock,
                buyPrice,
                msrp,
            )

            result = db.insert_product(product_info)

            if result:
                flash(f"Product {productCode} created successfully.", "success")
                return redirect(url_for("products_list"))
            else:
                flash("An error occurred while creating the product.", "danger")
                return render_template(
                    "product_form.html",
                    errors=["Database error while inserting product."],
                    form=request.form,
                    mode="create",
                )

        # GET
        return render_template("product_form.html", mode="create")

    # --- Edit existing product ---
    @app.route("/products/<product_code>/edit", methods=["GET", "POST"])
    def edit_product(product_code):
        if not _require_employee():
            return redirect(url_for("index"))

        # Fetch existing product
        product = db.get_single_product(product_code)
        if not product:
            flash(f"Product {product_code} not found.", "warning")
            return redirect(url_for("products_list"))

        if request.method == "POST":
            productName = request.form.get("productName", "").strip()
            productLine = request.form.get("productLine", "").strip()
            productScale = request.form.get("productScale", "").strip()
            productVendor = request.form.get("productVendor", "").strip()
            productDescription = request.form.get("productDescription", "").strip()
            quantityInStock_raw = request.form.get("quantityInStock", "").strip()
            buyPrice_raw = request.form.get("buyPrice", "").strip()
            msrp_raw = request.form.get("MSRP", "").strip()

            errors = []

            # Required checks
            if not (productName and productLine and productScale and productVendor and
                    productDescription and quantityInStock_raw and buyPrice_raw and
                    msrp_raw):
                errors.append("All fields are required.")

            # Length checks
            if len(productName) > 70:
                errors.append("Product name cannot exceed 70 characters.")
            if len(productLine) > 50:
                errors.append("Product line cannot exceed 50 characters.")
            if len(productScale) > 10:
                errors.append("Product scale cannot exceed 10 characters.")
            if len(productVendor) > 50:
                errors.append("Product vendor cannot exceed 50 characters.")

            # Numeric conversions
            quantityInStock = None
            buyPrice = None
            msrp = None

            if quantityInStock_raw:
                try:
                    quantityInStock = int(quantityInStock_raw)
                    if quantityInStock < 0:
                        errors.append("Quantity in stock cannot be negative.")
                except ValueError:
                    errors.append("Quantity in stock must be an integer.")

            if buyPrice_raw:
                try:
                    buyPrice = float(buyPrice_raw)
                    if buyPrice <= 0:
                        errors.append("Buy price must be positive.")
                except ValueError:
                    errors.append("Buy price must be a valid number.")

            if msrp_raw:
                try:
                    msrp = float(msrp_raw)
                    if msrp <= 0:
                        errors.append("MSRP must be positive.")
                except ValueError:
                    errors.append("MSRP must be a valid number.")

            if buyPrice is not None and msrp is not None and msrp < buyPrice:
                errors.append("MSRP should not be lower than buy price.")

            # Check productLine exists
            if productLine:
                line = db.execute_query(
                    "SELECT productLine FROM productlines WHERE productLine = %s",
                    (productLine,),
                    fetchone=True,
                )
                if not line:
                    errors.append("Product line does not exist.")

            if errors:
                # Use request.form for repopulation
                form_data = request.form
                return render_template(
                    "product_form.html",
                    errors=errors,
                    form=form_data,
                    mode="edit",
                    product_code=product_code,
                )

            # Perform update
            result = db.update_product(
                product_code,
                productName,
                productLine,
                productScale,
                productVendor,
                productDescription,
                quantityInStock,
                buyPrice,
                msrp,
            )

            if result:
                flash(f"Product {product_code} updated successfully.", "success")
                return redirect(url_for("products_list"))
            else:
                flash("No changes were made or an error occurred.", "warning")

        # GET: prefill with existing product data
        return render_template(
            "product_form.html",
            mode="edit",
            product_code=product_code,
            product=product,
        )

    # --- Delete product ---
    @app.route("/products/<product_code>/delete", methods=["GET", "POST"])
    def delete_product_route(product_code):
        if not _require_employee():
            return redirect(url_for("index"))

        product = db.get_single_product(product_code)
        if not product:
            flash(f"Product {product_code} not found.", "warning")
            return redirect(url_for("products_list"))

        if request.method == "POST":
            # Optional: you can add a confirmation checkbox here
            try:
                result = db.delete_product(product_code)
                if result:
                    flash(f"Product {product_code} deleted successfully.", "success")
                else:
                    flash("Could not delete product (maybe referenced in orders).", "danger")
            except Exception as e:
                print(f"Delete error: {e}")
                flash("An error occurred while deleting the product.", "danger")

            return redirect(url_for("products_list"))

        # GET: show confirmation page
        return render_template(
            "product_confirm_delete.html",
            product=product,
        )