from flask import render_template, request, redirect, url_for, flash, session, request
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
        search_query = request.args.get("search", "").strip()
        sort_order = request.args.get("sort", "none")   # "asc", "desc", or "none"

        
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
            raw_customers = db.get_assigned_customers(employee_number, search_query, sort_order)
            # Calculate balance manually since we aren't using the bulk fetch
            for c in raw_customers:
                bal = db.get_customer_balance(c["customerNumber"])
                c['balance'] = bal["balance"]
                customers.append(c)
        else:
            # Managers -> ALL customers (This function must exist in db_helper.py!)
            customers = db.get_all_customers_with_balance(search_query, sort_order)
            
            # Fetch offices for the Add Employee form
            offices = db.get_all_offices()

        # 3. Fetch Reports
        my_reports = db.get_employee_reports(employee_number)
        team_reports = db.get_subordinate_reports(employee_number)
        
        subordinates = []
        analytics_matrix = []
        unproductive_employees = []

        # Analytics Pagination
        analytics_page = request.args.get("analytics_page", 1, type=int)
        limit = 10
        offset = (analytics_page - 1) * limit

        if is_manager:
            subordinates = db.get_subordinates(employee_number)
            try:
                # New Analytics Features with Pagination
                analytics_matrix = db.get_employee_performance_matrix(limit=limit, offset=offset)
                unproductive_employees = db.get_unproductive_employees()
            except Exception as e:
                print(f"Analytics Error: {e}")

        return render_template("dashboard.html",
                               customers=customers,
                               search_query=search_query,
                               sort_order=sort_order,
                               my_reports=my_reports,
                               team_reports=team_reports,
                               subordinates=subordinates,
                               analytics_matrix=analytics_matrix,
                               unproductive_employees=unproductive_employees,
                               analytics_page=analytics_page,
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

        if session.get("user_type") != "employee":
            flash("Access denied.", "danger")
            return redirect(url_for("login"))

        filters = {
            'status': request.args.getlist('status'),
            'categories': request.args.getlist('category'),
            'price_ranges': request.args.getlist('price'),
            'sort_date': request.args.get('sort_date', 'newest')
        }

        orders = db.get_filtered_orders(customer_num, filters)

        product_lines = db.execute_query("SELECT productLine FROM productlines")
        
        customer = db.get_customer_details(customer_num)

        return render_template(
            "employee_customer_orders.html", 
            orders=orders,
            product_lines=product_lines,
            current_filters=filters,
            customer=customer,   
            customer_num=customer_num 
        )

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
        if session.get("user_type") != "employee":
            return redirect(url_for("login"))


        order_stats = db.get_office_order_stats()
        activity_stats = db.get_offices_activity_report()

        grand_total_sales = sum(item['total_sales'] for item in order_stats) if order_stats else 0

        return render_template("office_stats.html", 
                               order_stats=order_stats, 
                               activity_stats=activity_stats,
                               grand_total_sales=grand_total_sales)

    @app.route("/payment/edit/<int:customer_number>/<string:check_number>", methods=["GET", "POST"])
    def edit_payment(customer_number, check_number):
        if session.get("user_type") != "employee":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("index"))

        payment = db.get_payment_details(customer_number, check_number)
        if not payment:
            flash("Payment not found.", "danger")
            return redirect(url_for("employee_view_customer_orders", customer_num=customer_number))

        if request.method == "POST":
            new_amount = request.form.get("amount")
            new_check_number = request.form.get("checkNumber") 

            try:
                db.update_payment(customer_number, check_number, new_check_number, new_amount)
                flash("Payment updated successfully.", "success")
                return redirect(url_for("employee_view_customer_orders", customer_num=customer_number))
            except Exception as e:
                flash(f"Error updating payment: {e}", "danger")

        return render_template("edit_payment.html", payment=payment)

    @app.route("/payment/delete/<int:customer_number>/<string:check_number>", methods=["POST"])
    def delete_payment_route(customer_number, check_number):
        if session.get("user_type") != "employee":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("index"))

        try:
            db.delete_payment(customer_number, check_number)
            flash("Payment deleted successfully.", "success")
        except Exception as e:
            flash(f"Error deleting payment: {e}", "danger")
        
        return redirect(url_for("employee_view_customer_orders", customer_num=customer_number))
    
    @app.route("/payment/analysis")
    def payment_analysis_report():
        if session.get("user_type") != "employee":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("index"))
        city_param = request.args.get("city", "").strip()
        year_param = request.args.get("year", "").strip()
        line_param = request.args.get("product_line", "").strip()

        offices_list = db.get_all_offices()
        lines_list = db.get_all_product_lines()


        report_data = db.get_complex_payment_report(
            city_filter=city_param, 
            year_filter=year_param, 
            product_line_filter=line_param
        ) or []
        
        return render_template("payment_report.html", 
                               report_data=report_data, 
                               search_city=city_param, 
                               search_year=year_param,
                               search_line=line_param, 
                               offices=offices_list,
                               product_lines=lines_list)