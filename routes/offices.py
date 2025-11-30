from flask import render_template, request, redirect, url_for, flash, session

db = None

def init_office_routes(app, database):
    global db
    db = database

    def is_president():
        """Helper to check if current user is President."""
        return session.get("user_type") == "employee" and session.get("job_title") == "President"

    @app.route("/offices/add", methods=["GET", "POST"])
    def add_office():
        # Security Check
        if not is_president():
            flash("Access Denied. Only the President can add offices.", "danger")
            return redirect(url_for("index"))

        if request.method == "POST":
            # Collect form data
            code = request.form.get("officeCode", "").strip()
            city = request.form.get("city", "").strip()
            phone = request.form.get("phone", "").strip()
            addr1 = request.form.get("addressLine1", "").strip()
            addr2 = request.form.get("addressLine2", "").strip()
            state = request.form.get("state", "").strip()
            country = request.form.get("country", "").strip()
            postal = request.form.get("postalCode", "").strip()
            territory = request.form.get("territory", "").strip()

            # Validation
            if not (code and city and phone and addr1 and country and postal and territory):
                flash("Please fill in all required fields.", "warning")
                return render_template("office_form.html", mode="add", form=request.form)

            # Check duplicate ID
            if db.get_office_by_code(code):
                flash(f"Office Code '{code}' already exists.", "danger")
                return render_template("office_form.html", mode="add", form=request.form)

            try:
                # address2 and state can be None/Empty string
                data = (code, city, phone, addr1, addr2, state, country, postal, territory)
                db.insert_office(data)
                flash("New office added successfully!", "success")
                return redirect(url_for("index"))
            except Exception as e:
                flash(f"Error adding office: {e}", "danger")

        return render_template("office_form.html", mode="add")

    @app.route("/offices/edit/<office_code>", methods=["GET", "POST"])
    def edit_office(office_code):
        # Security Check
        if not is_president():
            flash("Access Denied.", "danger")
            return redirect(url_for("index"))

        office = db.get_office_by_code(office_code)
        if not office:
            flash("Office not found.", "danger")
            return redirect(url_for("index"))

        if request.method == "POST":
            # Collect mutable data
            phone = request.form.get("phone", "").strip()
            addr1 = request.form.get("addressLine1", "").strip()
            addr2 = request.form.get("addressLine2", "").strip()
            state = request.form.get("state", "").strip()
            postal = request.form.get("postalCode", "").strip()
            territory = request.form.get("territory", "").strip()

            if not (phone and addr1 and postal and territory):
                flash("Required fields cannot be empty.", "warning")
                return render_template("office_form.html", mode="edit", office=office)

            db.update_office(office_code, phone, addr1, addr2, state, postal, territory)
            flash(f"Office {office_code} updated successfully.", "success")
            return redirect(url_for("index"))

        return render_template("office_form.html", mode="edit", office=office)

    @app.route("/offices/delete/<office_code>", methods=["POST"])
    def delete_office_route(office_code):
        # Security Check
        if not is_president():
            flash("Access Denied.", "danger")
            return redirect(url_for("index"))

        success, message = db.delete_office(office_code)
        
        if success:
            flash(message, "success")
        else:
            flash(message, "danger")
        
        return redirect(url_for("index"))