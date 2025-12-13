from flask import render_template, request, redirect, url_for, flash, session

db = None


def init_order_routes(app, database):
    """Initialize order-related routes."""
    global db
    db = database

    @app.route("/order/<int:order_number>/update_comment", methods=["POST"])
    def update_comment_route(order_number):
        if session.get("user_type") != "employee":
            flash("Access denied.", "danger")
            return redirect(url_for("order_detail", order_number=order_number))

        new_comment = request.form.get("new_comment", "").strip()
        db.update_order_comment(order_number, new_comment)

        order = db.get_order(order_number)
        customer_num = order['customerNumber']

        flash("Order note updated successfully.", "success")
        
        return redirect(url_for("employee_view_customer_orders", customer_num=customer_num))

    @app.route("/order/<int:order_number>")
    def order_detail(order_number):
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
            customer_of_order = db.get_customer_details(order["customerNumber"])
            if (
                not customer_of_order 
                or customer_of_order.get("salesRepEmployeeNumber") != user_number
            ):
                flash("Access denied. You are not the sales rep for this customer.", "danger")
                return redirect(url_for("employee_dashboard"))

        elif not user_type:
            flash("You must be logged in to view order details.", "danger")
            return redirect(url_for("login"))

        order_items = db.get_order_details(order_number)

        return render_template(
            "order_detail.html",
            order=order,
            items=order_items
        )

    @app.route("/order/<int:order_number>/cancel", methods=["POST"])
    def cancel_order(order_number):
        user_type = session.get("user_type")
        user_number = session.get("user_number")

        if not user_type:
            flash("You must be logged in.", "danger")
            return redirect(url_for("login"))

        order = db.get_order(order_number)
        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for("index"))

        if user_type == "customer":
            if order["customerNumber"] != user_number:
                flash("You cannot cancel someone else's order.", "danger")
                return redirect(url_for("customer_orders"))

            if order["status"] != "In Process":
                flash("This order can no longer be cancelled.", "warning")
                return redirect(url_for("order_detail", order_number=order_number))

        db.execute_query(
            "UPDATE orders SET status = 'Cancelled' WHERE orderNumber = %s",
            (order_number,)
        )
        

        flash(f"Order #{order_number} has been cancelled.", "warning")
        return redirect(url_for("order_detail", order_number=order_number))


    @app.route("/order/item/<int:detail_id>/update", methods=["POST"])
    def update_order_item(detail_id):
        # 1. Security Check
        if not session.get("user_number"):
            flash("Please log in.", "danger")
            return redirect(url_for("login"))

        try:
            new_quantity = int(request.form.get("quantity"))
        except (ValueError, TypeError):
            new_quantity = 1
        
        item = db.get_order_detail_by_id(detail_id)
        if not item:
            flash("Item not found.", "danger")
            return redirect(url_for("index"))

        order = db.get_order(item['orderNumber'])
        if order['status'] != 'In Process':
            flash("Cannot update items in a processed order.", "danger")
            return redirect(url_for("order_detail", order_number=item['orderNumber']))

        if new_quantity > 0:
            db.update_order_item_quantity(detail_id, new_quantity)
            flash("Quantity updated.", "success")
        else:
            flash("Quantity must be at least 1.", "warning")

        return redirect(url_for("order_detail", order_number=item['orderNumber']))

    @app.route("/order/item/<int:detail_id>/delete", methods=["POST"])
    def delete_order_item(detail_id):
        if not session.get("user_number"):
            flash("Please log in.", "danger")
            return redirect(url_for("login"))

        item = db.get_order_detail_by_id(detail_id)
        if not item:
            flash("Item not found.", "danger")
            return redirect(url_for("index"))

        order_number = item['orderNumber']
        order = db.get_order(order_number)
        
        if order['status'] != 'In Process':
            flash("Cannot remove items from a processed order.", "danger")
            return redirect(url_for("order_detail", order_number=order_number))

        db.delete_order_item(detail_id)

        remaining_items = db.get_order_details(order_number)
        
        if not remaining_items:
            # The order is now empty. Autocancel it.
            db.execute_query(
                "UPDATE orders SET status = 'Cancelled', comments = 'Auto-cancelled: All items removed.' WHERE orderNumber = %s",
                (order_number,)
            )
            flash(f"Order #{order_number} has been cancelled because it is empty.", "warning")
            # Redirect to the dashboard/orders list, NOT the empty order page
            return redirect(url_for("customer_orders"))
        flash("Item removed from order.", "success")
        return redirect(url_for("order_detail", order_number=order_number))