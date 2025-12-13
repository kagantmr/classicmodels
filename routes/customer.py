from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import re, mysql


def init_customer_routes(app, database):
    """Initialize customer-specific routes."""
    global db
    db = database

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
        balance_info = db.get_customer_balance(customerNumber)
        payments = db.get_customer_payments(customerNumber)

        return render_template(
            "customerpage.html",
            customer=customer_details,
            balance=balance_info,
            payments=payments
        )

    @app.route("/customer/orders")
    def customer_orders():
        """Shows the logged-in customer's order history."""
        if session.get("user_type") != "customer":
            flash("You must be a customer to view this page.", "danger")
            return redirect(url_for("index"))

        customerNumber = session.get("user_number")
       
        # take sort parameter (default is newest) 
        sort_option = request.args.get('sort', 'newest') 
        
        if not customerNumber:
            flash("Error finding your profile. Please log in again.", "danger")
            return redirect(url_for('login'))
        
        # send sort request to database
        orders = db.get_customer_orders(customerNumber, sort_by=sort_option)
        
        return render_template("customer_orders.html", orders=orders, sort_option=sort_option)
    
    @app.route("/customer/signup", methods=["GET","POST"])
    def customer_signup():
        if request.method == "POST":

            # get inputs
            fname = request.form.get("contactFirstName","").strip()
            lname = request.form.get('contactLastName', '').strip()
            cname = request.form.get('customerName', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('addressLine1', '').strip()
            city = request.form.get('city', '').strip()
            country = request.form.get('country', '').strip()
            password = request.form.get('password', '')

            errors = [] # collect all errors

            # validation

            if not fname or not lname or not cname or not phone or not address or not city or not country:
                errors.append("All fields are required.")

            # Name validation
            if len(fname) < 2 or len(lname) < 2:
                errors.append("First and last name must be at least 2 characters.")

            # Phone number check (digits only)
            if not re.match(r'^[0-9\-\+\s]{6,20}$', phone):
                errors.append("Phone number format is invalid.")

            # length check
            if len(fname) > 50 or len(lname) > 50 or len(cname) > 50 or len(address) > 50 or len(city) > 50 or len(country) > 50:
                errors.append("Exceed maximum char limit 50")

            # Password length
            if len(password) < 6:
                errors.append("Password must be at least 6 characters long.")

            # check duplicates in DB
            same_phone = db.execute_query("SELECT customerNumber FROM customers WHERE phone=%s",(phone,))

            if same_phone:
                errors.append("Phone number is already used")

            # if errors re render page
            if errors:
                return render_template("customer_signup.html",errors=errors,form=request.form)
            
            # if everthing is valid create customer


            #auto assign new customer number
            max_row = db.execute_query("SELECT MAX(customerNumber) as max_id FROM customers", fetchone=True)
            if max_row is None:
                new_id = 1
            else:
                new_id = max_row["max_id"] + 1


            
            # hash password
            hashed_pw = generate_password_hash(password)

            try:
                customer_data = (new_id, cname, lname, fname,
            phone, address, city, country)
                db.insert_customer(customer_data)
                customer_auth_data = (new_id, hashed_pw)
                db.insert_customer_to_auth(customer_auth_data)
                flash(f"Account created successfully! Please log in. Customer number is: {new_id}", "success")
                return redirect(url_for('login'))

            except mysql.connector.Error as err:
                flash("Something went wrong please try later")
        
        return render_template("customer_signup.html")


    @app.route("/delete-account", methods=["GET", "POST"])
    def delete_account():
        # Login check
        if session.get("user_type") != "customer":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("login"))

        customer_number = session.get("user_number")

        # GET request
        if request.method == "GET":
            # Debt Control again for Security
            balance_info = db.get_customer_balance(customer_number)
            if balance_info and balance_info["balance"] > 0:
                flash(f"Action Denied! You have an outstanding balance of ${balance_info['balance']}. Please pay first.", "danger")
                return redirect(url_for("account_settings"))
            
            return render_template("delete_account.html")

        # POST request
        if request.method == "POST":
            password_input = request.form.get("password")
            checkbox = request.form.get("confirm_checkbox")

            # Checkbox check
            if not checkbox:
                flash("You must check the confirmation box.", "warning")
                return redirect(url_for("delete_account"))

            # Password Check (use function from db_helper.py)
            user = db.check_customer_credentials(customer_number, password_input)
            
            if not user:
                flash("Incorrect password provided.", "danger")
                return redirect(url_for("delete_account"))

            # Debt check (for the last time)
            balance_info = db.get_customer_balance(customer_number)
            if balance_info and balance_info["balance"] > 0:
                flash("Cannot delete account due to outstanding debt.", "danger")
                return redirect(url_for("account_settings"))

            # Deleting opertaion via Transaction
            success = db.delete_customer_transaction(customer_number)

            if success:
                # Cleane session and logout
                session.clear()
                flash("Your account has been permanently deleted. We are sorry to see you go.", "info")
                return redirect(url_for("login"))
            else:
                flash("An error occurred while deleting your account. Please contact support.", "danger")
                return redirect(url_for("account_settings"))

    
    @app.route("/customer/update_profile", methods=["POST"])
    def update_customer_profile_route():
        if session.get("user_type") != "customer":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("login"))

        customer_number = session.get("user_number")

        # Take data from form
        fname = request.form.get("contactFirstName", "").strip()
        lname = request.form.get("contactLastName", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("addressLine1", "").strip()
        city = request.form.get("city", "").strip()
        country = request.form.get("country", "").strip()

        # Validation for empty datas
        if not fname or not lname or not phone or not address or not city or not country:
            flash("All fields are required for profile update.", "warning")
            return redirect(url_for("account_settings"))

        # UPDATE database
        try:
            db.update_customer_profile(customer_number, fname, lname, phone, address, city, country)
            
            # Updates on Session
            session["user_name"] = fname
            
            flash("Profile updated successfully!", "success")
        except Exception as e:
            print(f"Update Error: {e}")
            flash("An error occurred while updating your profile.", "danger")

        return redirect(url_for("account_settings"))
            

    @app.route("/payment/make", methods=["GET", "POST"])
    def make_payment():
        # 1. Security Check: Must be logged in as a customer
        if not session.get("user_number") or session.get("user_type") != 'customer':
            flash("You must be logged in as a customer to make a payment.", "danger")
            return redirect(url_for("login"))
        
        customer_number = session.get("user_number")

        if request.method == "POST":
            check_number = request.form.get("checkNumber").strip()
            amount_str = request.form.get("amount")

            # 2. Validation (Rubric requirement)
            try:
                amount = float(amount_str)
                if amount <= 0:
                    flash("Amount must be a positive number.", "danger")
                    return render_template("make_payment.html", checkNumber=check_number, amount=amount_str)
            except (ValueError, TypeError):
                flash("Invalid amount entered.", "danger")
                return render_template("make_payment.html", checkNumber=check_number, amount=amount_str)

            if not check_number or len(check_number) < 5:
                flash("Please enter a valid check number/transaction ID (at least 5 characters).", "danger")
                return render_template("make_payment.html", checkNumber=check_number, amount=amount)

            # 3. Action: Insert into DB
            db.create_payment(customer_number, check_number, amount)
            flash(f"Payment of ${amount:.2f} recorded successfully.", "success")
            
            # Redirect to the profile page to see the new payment in the history
            return redirect(url_for("customer_profile")) 

        # GET request: Render the form
        return render_template("make_payment.html")
