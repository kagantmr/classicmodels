from flask import render_template, request, redirect, url_for, flash, session
from db_helper import DatabaseHandler

db = None


def init_auth_routes(app, database):
    """Initialize auth routes."""
    global db
    db = database

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            number_input = request.form.get("number")
            password_input = request.form.get("password")
            user_type = request.form.get("user_type")

            if not number_input.isdigit():
                flash("Please enter a valid number!", "danger")
                return redirect(url_for("login"))
            
            if not password_input:
                flash("Password is required.", "danger")
                return redirect(url_for("login"))

            number_input = int(number_input)
            
            if user_type == "customer":
                customer = db.check_customer_credentials(number_input, password_input)
                
                if customer:
                    session["user_type"] = "customer"
                    session["user_number"] = customer["customerNumber"]
                    session["user_name"] = customer["contactFirstName"]
                    flash("Login successful as Customer!", "success")
                    return redirect(url_for('index'))
                else:
                    flash("Invalid customer number or password.", "danger")

            elif user_type == "employee":
                employee = db.check_employee_credentials(number_input, password_input)
                
                if employee:
                    session["user_type"] = "employee"
                    session["user_number"] = employee["employeeNumber"]
                    session["user_name"] = employee["firstName"]
                    # JobTitle data inserting to session!
                    session["job_title"] = employee["jobTitle"] 
                    
                    flash(f"Login successful as {employee['jobTitle']}!", "info")
                    return redirect(url_for('index'))
                else:
                    flash("Invalid employee number or password.", "danger")
            
            else:
                flash("Invalid login attempt.", "danger")

            return redirect(url_for("login"))
        
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out", "info")
        return redirect(url_for("login"))

    @app.route("/change_password", methods=["GET", "POST"])
    def change_password():
        from werkzeug.security import generate_password_hash
        
        if "user_type" not in session:
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

            hashed_pw = generate_password_hash(new_password)

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

            session.clear()
            flash("Password changed successfully! Please log in again.", "success")
            return redirect(url_for("login"))

        return render_template("change_password.html")

    @app.route("/account/settings")
    def account_settings():
        if "user_type" not in session:
            flash("You need to log in first.", "warning")
            return redirect(url_for("login"))

        user_type = session["user_type"]
        user_number = session["user_number"]

        # Fetch user info depending on type
        if user_type == "customer":
            user = db.get_customer_details(user_number)
        else:
            user = db.execute_query(
                "SELECT * FROM employees WHERE employeeNumber = %s",
                (user_number,),
                fetchone=True
            )

        return render_template("account_settings.html", user=user, user_type=user_type)
