from flask import render_template, request, redirect, url_for, flash, session

db = None


def init_employee_routes(app, database):
    """Initialize employee-specific routes."""
    global db
    db = database

# In routes/employee.py

    @app.route("/dashboard")
    def employee_dashboard():
        if session.get("user_type") != "employee":
            flash("You must be an employee to view the dashboard.", "danger")
            return redirect(url_for("index"))

        employee_number = session.get("user_number")
        
        # 1. Determine Role
        employee_details = db.get_employee_details(employee_number)
        
        # Check if they are strictly a 'Sales Rep'
        is_sales_rep = (employee_details['jobTitle'] == 'Sales Rep')
        
        # Anyone who is NOT a Sales Rep is considered a Manager (President, VP, etc.)
        is_manager = not is_sales_rep 

        customers = []
        
        # 2. Fetch Customers
        if is_sales_rep:
            # Sales Reps -> Only assigned customers
            raw_customers = db.get_assigned_customers(employee_number)
            # Calculate balance manually since we aren't using the bulk fetch
            for c in raw_customers:
                bal = db.get_customer_balance(c["customerNumber"])
                c['balance'] = bal["balance"]
                customers.append(c)
        else:
            # Managers -> ALL customers (This function must exist in db_helper.py!)
            customers = db.get_all_customers_with_balance()

        # 3. Fetch Reports
        my_reports = db.get_employee_reports(employee_number)
        team_reports = db.get_subordinate_reports(employee_number)
        
        subordinates = []
        if is_manager:
            subordinates = db.get_subordinates(employee_number)

        # 4. PASS 'is_manager' TO THE TEMPLATE
        return render_template("dashboard.html",
                               customers=customers,
                               my_reports=my_reports,
                               team_reports=team_reports,
                               subordinates=subordinates,
                               is_sales_rep=is_sales_rep,
                               is_manager=is_manager)

# In routes/employee.py

    @app.route("/employee/customer_orders/<int:customer_num>")
    def employee_view_customer_orders(customer_num):
        """View a customer's orders. Permissions vary by role."""
        if session.get("user_type") != "employee":
            flash("You must be an employee to view this page.", "danger")
            return redirect(url_for("login"))

        employee_number = session.get("user_number")
        
        # 1. Fetch Employee Details to check Role
        emp = db.get_employee_details(employee_number)
        if not emp:
            flash("Employee record not found.", "danger")
            return redirect(url_for("index"))

        # Define "Management" based on your list (Anyone who is NOT a Sales Rep)
        # Your list included Presidents, VPs, and Managers. The only ones excluded were Sales Reps.
        is_manager = (emp['jobTitle'] != 'Sales Rep')

        # 2. Access Control: Can this user view this customer?
        if not is_manager:
            # Sales Reps can ONLY see their assigned customers
            my_customers_data = db.get_assigned_customers(employee_number)
            my_customers = my_customers_data if my_customers_data is not None else []
            
            if not any(c['customerNumber'] == customer_num for c in my_customers):
                flash("You are not authorized to view this customer.", "warning")
                return redirect(url_for("employee_dashboard"))
        
        # (Managers can view ANY customer, so we skip the check for them)

        # 3. Fetch Basic Data
        details = db.get_customer_details(customer_num)
        orders = db.get_customer_orders(customer_num)
        balance = db.get_customer_balance(customer_num)
        
        # 4. Payment Visibility Control
        # Only Managers/VPs can see payments
        payments = []
        if is_manager:
            payments = db.get_customer_payments(customer_num)

        return render_template("employee_customer_orders.html",
                               customer=details,
                               orders=orders,
                               balance=balance,
                               payments=payments,
                               is_manager=is_manager) # Pass this flag to the UI

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
    

    @app.route("/admin/payment/delete", methods=["POST"])
    def delete_payment():
        """Allows Managers/VPs to delete a payment."""
        if session.get("user_type") != "employee":
            return redirect(url_for("login"))

        # 1. Role Check
        emp = db.get_employee_details(session.get("user_number"))
        if emp['jobTitle'] == 'Sales Rep':
            flash("Access Denied: Only Managers can delete payments.", "danger")
            return redirect(url_for("employee_dashboard"))

        # 2. Get Data
        customer_num = request.form.get("customer_number")
        check_num = request.form.get("check_number")

        # 3. Execute Delete
        db.delete_payment(customer_num, check_num)
        
        flash(f"Payment {check_num} deleted successfully.", "warning")
        return redirect(url_for("employee_view_customer_orders", customer_num=customer_num))

# --- Add to routes/employee.py ---

    @app.route("/admin/payment/edit/<int:customer_num>/<string:check_num>", methods=["GET", "POST"])
    def edit_payment(customer_num, check_num):
        # 1. Security Check (Managers Only)
        if session.get("user_type") != "employee":
            return redirect(url_for("login"))
        
        emp = db.get_employee_details(session.get("user_number"))
        if emp['jobTitle'] == 'Sales Rep':
            flash("Access Denied.", "danger")
            return redirect(url_for("employee_dashboard"))

        # 2. Handle Form Submission
        if request.method == "POST":
            new_check_num = request.form.get("checkNumber")
            new_amount = request.form.get("amount")
            
            if not new_check_num or not new_amount:
                flash("All fields are required.", "warning")
            else:
                db.update_payment(customer_num, check_num, new_check_num, new_amount)
                flash("Payment updated successfully.", "success")
                return redirect(url_for("employee_view_customer_orders", customer_num=customer_num))

        # 3. Render Edit Page
        payment = db.get_payment_details(customer_num, check_num)
        return render_template("edit_payment.html", payment=payment)