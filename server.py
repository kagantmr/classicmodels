from flask import Flask, render_template, request, redirect, url_for, flash, session
from db_helper import DatabaseHandler
import mysql.connector
from os import getenv
from dotenv import load_dotenv # Import load_dotenv

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
    product = db.get_single_product(product_code)[0]
    #print(product)

    if not product:
        return "Product not found", 404
    
    return render_template("product.html", product=product)

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        number_input = request.form.get("number")
        user_type = request.form.get("user_type") # Get the user type from hidden input

        if not number_input.isdigit():
            flash("Please enter a valid number!", "danger")
            return redirect(url_for("login"))

        number_input = int(number_input)
        
        if user_type == "customer":
            customer = db.check_customer_number(number_input)
            if customer:
                # store customer info in session
                session["user_type"] = "customer"
                session["user_number"] = customer["customerNumber"]
                session["user_name"] = customer["contactFirstName"]
                flash("Login successful as Customer!", "success")
                return redirect(url_for('index')) # Redirect to home
            else:
                flash("Customer number not found!", "danger")

        elif user_type == "employee":
            employee = db.check_employee_number(number_input)
            if employee:
                session["user_type"] = "employee"
                session["user_number"] = employee["employeeNumber"]
                session["user_name"] = employee["firstName"] 
                flash(f"Login successful as Employee: {employee['jobTitle']}!", "info")
                return redirect(url_for('index')) # Redirect to home
            else:
                flash("Employee number not found!", "danger")
        
        else:
            flash("Invalid login attempt.", "danger")

        return redirect(url_for("login"))
    
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
    my_customers = db.get_assigned_customers(session.get("user_number"))
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

    # If customer: ensure owns the order
    if session.get("user_type") == "customer":
        if order["customerNumber"] != session.get("user_number"):
            flash("Access denied.", "danger")
            return redirect(url_for("index"))

    # If employee: optionally verify assignment
    if session.get("user_type") == "employee":
        pass

    order_items = db.get_order_details(order_number)
    payments = db.get_order_payments(order_number)
    return render_template("order_detail.html", order=order, items=order_items, payments=payments)


if __name__ == '__main__':
    app.run(debug=True)