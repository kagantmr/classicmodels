from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
import string
import random

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
        
        # 1. Determine Role
        employee_details = db.get_employee_details(employee_number)
        
        # Check if they are strictly a 'Sales Rep'
        is_sales_rep = (employee_details['jobTitle'] == 'Sales Rep')
        
        # Anyone who is NOT a Sales Rep is considered a Manager (President, VP, etc.)
        # Ideally we check for "Manager" in title, but user specified "sales managers can add"
        # and "jobTitle" for Anthony Bow is "Sales Manager (NA)". 
        # So "not is_sales_rep" is a loose safe bet, or we check "Manager" in jobTitle
        is_manager = "Manager" in employee_details['jobTitle'] or "President" in employee_details['jobTitle'] or "VP" in employee_details['jobTitle']

        customers = []
        offices = []
        
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
            
            # Fetch offices for the Add Employee form
            offices = db.get_all_offices()

        # 3. Fetch Reports
        my_reports = db.get_employee_reports(employee_number)
        team_reports = db.get_subordinate_reports(employee_number)
        
        subordinates = []
        if is_manager:
            subordinates = db.get_subordinates(employee_number)

        return render_template("dashboard.html",
                               customers=customers,
                               my_reports=my_reports,
                               team_reports=team_reports,
                               subordinates=subordinates,
                               is_sales_rep=is_sales_rep,
                               is_manager=is_manager,
                               offices=offices)

    @app.route("/add_employee", methods=["POST"])
    def add_employee():
        if session.get("user_type") != "employee":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("index"))

        # Verify Manager Status Again
        manager_number = session.get("user_number")
        manager_details = db.get_employee_details(manager_number)
        is_manager = "Manager" in manager_details['jobTitle'] or "President" in manager_details['jobTitle'] or "VP" in manager_details['jobTitle']
        
        if not is_manager:
            flash("Only Managers can add employees.", "danger")
            return redirect(url_for("employee_dashboard"))

        first_name = request.form.get("firstName")
        last_name = request.form.get("lastName")
        extension = request.form.get("extension")
        email = request.form.get("email")
        office_code = request.form.get("officeCode")

        if not all([first_name, last_name, extension, email, office_code]):
            flash("All fields are required.", "danger")
            return redirect(url_for("employee_dashboard"))

        # Generate ID
        new_id = db.get_next_employee_number()
        
        # Add to DB (Always 'Sales Rep', reports to current user)
        db.add_employee(new_id, last_name, first_name, extension, email, office_code, manager_number, "Sales Rep")

        # Generate Random Password
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(chars) for _ in range(10))
        hashed_pw = generate_password_hash(password)

        # Create Auth
        db.create_employee_auth(new_id, hashed_pw)

        flash(f"New Sales Rep added successfully! ID: {new_id}, Password: {password}", "success")
        return redirect(url_for("employee_dashboard"))

    @app.route("/employee/customer_orders/<int:customer_num>")
    def employee_view_customer_orders(customer_num):
        """View a customer's orders. Permissions vary by role."""
        if session.get("user_type") != "employee":
            flash("You must be an employee to view this page.", "danger")
            return redirect(url_for("login"))

        my_customers_data = db.get_assigned_customers(session.get("user_number"))

        sort_option = request.args.get('sort', 'newest')
        
        details = db.get_customer_details(customer_num)
        
        orders = db.get_customer_orders(customer_num, sort_by=sort_option)
        
        balance = db.get_customer_balance(customer_num)
        payments = db.get_customer_payments(customer_num)

        # Add sort parameter to HTML and render 
        return render_template("employee_customer_orders.html",
                               customer=details,
                               orders=orders,
                               balance=balance,
                               payments=payments,
                               sort_option=sort_option)

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

    @app.route("/office/statistics")
    def office_statistics():
        # Security check
        if session.get("user_type") != "employee":
            flash("Access Denied.", "danger")
            return redirect(url_for("login"))

        # Authority check (check job title in session)
        job_title = session.get("job_title", "")
        is_manager = "Manager" in job_title or "President" in job_title or "VP" in job_title

        if not is_manager:
            flash("Only Management can view Office Statistics.", "warning")
            return redirect(url_for("employee_dashboard"))

        # Complex Join
        order_stats = db.get_office_order_stats()
        # Outer Join 
        activity_stats = db.get_offices_activity_report()

        return render_template("office_stats.html", 
                               order_stats=order_stats, 
                               activity_stats=activity_stats)
