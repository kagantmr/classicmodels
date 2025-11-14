from flask import Flask, render_template, request, redirect, url_for, flash, session
from db_helper import DatabaseHandler
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey" # for flash messages

db = DatabaseHandler(password="Mutluluk07") # enter password

@app.route('/')
def index():
    query = ("SELECT productLine, textDescription FROM productlines")
    productlines = db.execute_query(query)
    return render_template('index.html', productlines=productlines)

# New route for productline pages
@app.route("/products/<product_line>")
def products_by_line(product_line):
    query = "SELECT * FROM products WHERE productLine = %s"
    products = db.execute_query(query, (product_line,))
    return render_template("products.html", products=products, product_line=product_line)


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        number_input = request.form.get("number")
        if not number_input.isdigit():
            flash("Please enter a valid number!", "danger")
            return redirect(url_for("login"))

        number_input = int(number_input)
        customer = db.check_customer_number(number_input)
        if customer:
            # store customer info in session
            session["user_type"] = "customer"
            session["user_number"] = customer["customerNumber"]
            flash("Login successful as Customer!", "success")
            return index()
        
        
        employee = db.check_employee_number(number_input)
        
        if employee:
            
            session["user_type"] = "employee"
            session["user_number"] = employee["employeeNumber"]
            flash(f"Login successful as Employee: {employee['jobTitle']}!", "info")
            return index()
        else:
            flash("Number not found!", "danger")

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

@app.route("/userprofile")
def userprofile():
    
    if session.get("user_type") != "customer":
        flash("You must be an customer to view the dashboard.", "danger")
        return redirect(url_for("index"))

    customerNumber = session.get("customer_number")
    
    
    return render_template("customerpage.html")


@app.route("/profile")
def my_profile():

    if not session.get("user_number"):
        flash("You need to log in to view your profile.", "danger")
        return redirect(url_for("login"))

    user_type = session.get("user_type")

    if user_type == "employee":
        # If the user is an employee, redirect to dashboard
        return redirect(url_for("employee_dashboard"))
        
    elif user_type == "customer":
        # If the user is a customer, redirect to user profile
        return redirect(url_for("userprofile"))

    else:
        flash("Your profile type is unknown.", "danger")
        return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(debug=True)