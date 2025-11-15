from flask import Flask, render_template, request, redirect, url_for, flash, session
from db_helper import DatabaseHandler
import mysql.connector
from os import getenv
from dotenv import load_dotenv # Import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash   #Import generate_password_hash, check_password_hash to hashing

load_dotenv() # Load variables from .env file at the top

app = Flask(__name__)
app.secret_key = "supersecretkey" # for flash messages


# get password from environment variable
db_password = getenv("DB_PASSWORD")

if not db_password:
    # this will stop the app if the password isn't found
    raise ValueError("DB_PASSWORD environment variable not set. Please create a .env file.")

db = DatabaseHandler(password=db_password) # pass the loaded password here

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/productlines')
def productlines():
    productlines_data = db.execute_query(("SELECT productLine, textDescription FROM productlines"))
    return render_template('productlines.html', productlines=productlines_data)

# New route for productline pages
@app.route("/products/<product_line>")
def products_by_line(product_line):
    query = "SELECT * FROM products WHERE productLine = %s"
    products = db.execute_query(query, (product_line,))
    return render_template("products.html", products=products, product_line=product_line)

# page for the single product
@app.route("/product/<product_code>")
def product_page(product_code):
    # FIX: db.get_single_product now uses fetchone, so no [0] needed.
    product = db.get_single_product(product_code)
    
    if not product:
        return "Product not found", 404
    
    return render_template("product.html", product=product)

# UPDATED: Full /login route
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        number_input = request.form.get("number")
        password_input = request.form.get("password") # NEW: Get password
        user_type = request.form.get("user_type") 

        if not number_input.isdigit():
            flash("Please enter a valid number!", "danger")
            return redirect(url_for("login"))
        
        if not password_input: # Check for empty password
            flash("Password is required.", "danger")
            return redirect(url_for("login"))

        number_input = int(number_input)
        
        if user_type == "customer":
            # UPDATED: Use new credentials check function
            customer = db.check_customer_credentials(number_input, password_input)
            
            if customer:
                # store customer info in session
                session["user_type"] = "customer"
                session["user_number"] = customer["customerNumber"]
                session["user_name"] = customer["contactFirstName"]
                flash("Login successful as Customer!", "success")
                return redirect(url_for('index')) # Redirect to home
            else:
                # Secure message:
                flash("Invalid customer number or password.", "danger")

        elif user_type == "employee":
            # UPDATED: Use new credentials check function
            employee = db.check_employee_credentials(number_input, password_input)
            
            if employee:
                session["user_type"] = "employee"
                session["user_number"] = employee["employeeNumber"]
                session["user_name"] = employee["firstName"] 
                flash(f"Login successful as Employee: {employee['jobTitle']}!", "info")
                return redirect(url_for('index')) # Redirect to home
            else:
                # Secure message:
                flash("Invalid employee number or password.", "danger")
        
        else:
            flash("Invalid login attempt.", "danger")

        # If login fails, redirect back to login
        return redirect(url_for("login"))
    
    # Handle GET request
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out","info")
    return redirect(url_for("login"))

@app.route("/dashboard")
def employee_dashboard():
    
    if session.get("user_type") != "employee":
        flash("You must be an employee to view the dashboard.", "danger")
        return redirect(url_for("index"))

    employee_number = session.get("user_number")
    
    customers = db.get_assigned_customers(employee_number)
    
    return render_template("dashboard.html", customers=customers)

@app.route("/employee/customer_orders/<int:customer_num>")
def employee_view_customer_orders(customer_num):
    # Security check: Only employees can access this
    if session.get("user_type") != "employee":
        flash("You must be an employee to view this page.", "danger")
        return redirect(url_for("login"))

    # Security check: Verify this employee is assigned to this customer
    # Note: db.get_assigned_customers might return None on error
    my_customers_data = db.get_assigned_customers(session.get("user_number"))
    my_customers = my_customers_data if my_customers_data is not None else []
    
    if not any(c['customerNumber'] == customer_num for c in my_customers):
         flash("You are not authorized to view this customer.", "warning")
         return redirect(url_for("employee_dashboard"))

    # Fetch data using helper functions
    details = db.get_customer_details(customer_num)
    orders = db.get_customer_orders(customer_num)

    return render_template("employee_customer_orders.html", customer=details, orders=orders)

@app.route("/customer/profile")
def customer_profile():
    """Shows the logged-in customer's profile details."""
    if session.get("user_type") != "customer":
        flash("You must be a customer to view this page.", "danger")
        return redirect(url_for("index"))

    customerNumber = session.get("user_number")
    
    if not customerNumber:
        flash("Error finding your profile. Please log in again.", "danger")
        return redirect(url_for('login'))
    
    customer_details = db.get_customer_details(customerNumber)
    
    return render_template("customerpage.html", customer=customer_details) # Renders customer profile


@app.route("/customer/orders")
def customer_orders():
    """Shows the logged-in customer's order history."""
    if session.get("user_type") != "customer":
        flash("You must be a customer to view this page.", "danger")
        return redirect(url_for("index"))

    customerNumber = session.get("user_number")
    
    if not customerNumber:
        flash("Error finding your profile. Please log in again.", "danger")
        return redirect(url_for('login'))
    
    orders = db.get_customer_orders(customerNumber)
    
    return render_template("customer_orders.html", orders=orders)


@app.route("/profile")
def my_profile():

    if not session.get("user_number"):
        flash("You need to log in to view your profile.", "danger")
        return redirect(url_for("login"))

    user_type = session.get("user_type")

    if user_type == "employee":
        return redirect(url_for("employee_dashboard")) # if the user is an employee, go to dashboard
        
    elif user_type == "customer":
        return redirect(url_for("customer_profile"))

    else:
        flash("Your profile type is unknown.", "danger")
        return redirect(url_for("index"))

@app.route("/order/<int:order_number>")
def order_detail(order_number):
    # Authorization: customer can see own orders; employee can see assigned customer's orders
    order = db.get_order(order_number)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("index"))

    user_type = session.get("user_type")
    user_number = session.get("user_number")

    if user_type == "customer":
        if order["customerNumber"] != user_number:
            flash("Access denied. This is not your order.", "danger")
            return redirect(url_for("index"))

    elif user_type == "employee":
        # SECURITY UPDATE: Check if employee is assigned to this order's customer
        customer_of_order = db.get_customer_details(order["customerNumber"])
        if not customer_of_order or customer_of_order.get("salesRepEmployeeNumber") != user_number:
            flash("Access denied. You are not the sales rep for this order's customer.", "danger")
            return redirect(url_for("employee_dashboard"))
    
    elif not user_type: # If not logged in at all
        flash("You must be logged in to view order details.", "danger")
        return redirect(url_for("login"))


    order_items = db.get_order_details(order_number)
    payments = db.get_order_payments(order_number)
    return render_template("order_detail.html", order=order, items=order_items, payments=payments)


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    
    if "user_type" not in session:   #Prevent unauthorized access
        flash("You need to log in first.", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not old_password or not new_password or not confirm_password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match!", "danger")
            return redirect(url_for("change_password"))

        user_type = session["user_type"]
        user_number = session["user_number"]

        
        if user_type == "customer":
            user = db.check_customer_credentials(user_number, old_password)
        else:
            user = db.check_employee_credentials(user_number, old_password)

        if not user:
            flash("Old password is incorrect!", "danger")
            return redirect(url_for("change_password"))

        # Hash the new password
        hashed_pw = generate_password_hash(new_password)

        # UPDATE DB
        if user_type == "customer":
            db.execute_query(
                "UPDATE customer_auth SET hashedPassword = %s WHERE customerNumber = %s",
                (hashed_pw, user_number)
            )
        else:
            db.execute_query(
                "UPDATE employee_auth SET hashedPassword = %s WHERE employeeNumber = %s",
                (hashed_pw, user_number)
            )

        # Logout and redirection
        session.clear()
        flash("Password changed successfully! Please log in again.", "success")
        return redirect(url_for("login"))

    return render_template("change_password.html")


if __name__ == '__main__':
    app.run(debug=True)