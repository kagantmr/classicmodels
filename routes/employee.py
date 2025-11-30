from flask import render_template, request, redirect, url_for, flash, session

db = None


def init_employee_routes(app, database):
    """Initialize employee-specific routes."""
    global db
    db = database

    @app.route("/dashboard")
    def employee_dashboard():
        if session.get("user_type") != "employee":
            flash("You must be an employee to view the dashboard.", "danger")
            return redirect(url_for("index"))

        employee_number = session.get("user_number")
        
        # Determine if user is a Sales Rep
        employee_details = db.get_employee_details(employee_number)
        is_sales_rep = False
        if employee_details and employee_details['jobTitle'] == 'Sales Rep':
            is_sales_rep = True

        customers = []
        customer_balances = []
        
        if is_sales_rep:
            customers = db.get_assigned_customers(employee_number)
            # Add customer balance info
            for c in customers:
                bal = db.get_customer_balance(c["customerNumber"])
                customer_balances.append({
                    "customerNumber": c["customerNumber"],
                    "customerName": c["customerName"],
                    "balance": bal["balance"]
                })

        my_reports = db.get_employee_reports(employee_number)
        team_reports = db.get_subordinate_reports(employee_number)
        
        # Fetch subordinates if not a Sales Rep
        subordinates = []
        if not is_sales_rep:
            subordinates = db.get_subordinates(employee_number)

        return render_template("dashboard.html",
                               customers=customers,
                               customer_balances=customer_balances,
                               my_reports=my_reports,
                               team_reports=team_reports,
                               subordinates=subordinates,
                               is_sales_rep=is_sales_rep)

    @app.route("/employee/customer_orders/<int:customer_num>")
    def employee_view_customer_orders(customer_num):
        """View a customer's orders from an employee perspective."""
        if session.get("user_type") != "employee":
            flash("You must be an employee to view this page.", "danger")
            return redirect(url_for("login"))

        my_customers_data = db.get_assigned_customers(session.get("user_number"))
        my_customers = my_customers_data if my_customers_data is not None else []
        
        if not any(c['customerNumber'] == customer_num for c in my_customers):
            flash("You are not authorized to view this customer.", "warning")
            return redirect(url_for("employee_dashboard"))

        details = db.get_customer_details(customer_num)
        orders = db.get_customer_orders(customer_num)
        balance = db.get_customer_balance(customer_num)
        payments = db.get_customer_payments(customer_num)

        return render_template("employee_customer_orders.html",
                               customer=details,
                               orders=orders,
                               balance=balance,
                               payments=payments)

    @app.route("/create_report", methods=["POST"])
    def create_report():
        """Create a new employee report."""
        if session.get("user_type") != "employee":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("index"))
            
        content = request.form.get("report_content")
        if not content:
            flash("Report content cannot be empty.", "danger")
            return redirect(url_for("employee_dashboard"))
            
        employee_number = session.get("user_number")
        db.create_report(employee_number, content)
        
        flash("Report submitted successfully!", "success")
        return redirect(url_for("employee_dashboard"))

    @app.route("/fire_employee/<int:employee_id>", methods=["POST"])
    def fire_employee(employee_id):
        """Fire a subordinate Sales Rep."""
        if session.get("user_type") != "employee":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("index"))

        # Optional: Check if the logged-in user is actually the manager of this employee
        # For now, we rely on the UI being hidden and the db_helper check
        
        success, message = db.fire_sales_rep(employee_id)
        
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
            
        return redirect(url_for("employee_dashboard"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            flash("Registration endpoint not fully implemented yet.", "info")
            return redirect(url_for("login"))
        return render_template("register.html")
