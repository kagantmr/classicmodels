import mysql.connector
from werkzeug.security import check_password_hash
from decimal import Decimal


class DatabaseHandler:
    def __init__(self, host="localhost", user="root", password="", database="classicmodels"):
        self.db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.db.cursor(dictionary=True)

    def check_customer_credentials(self, num, password):
        """Validates customerNumber and password. Returns customer data on success, else None."""
        query_hash = "SELECT hashedPassword FROM customer_auth WHERE customerNumber = %s"
        auth_data = self.execute_query(query_hash, (num,), fetchone=True)
        
        if auth_data and check_password_hash(auth_data['hashedPassword'], password):
            query_customer = "SELECT * FROM customers WHERE customerNumber = %s"
            return self.execute_query(query_customer, (num,), fetchone=True)
        
        return None
    
    def check_employee_credentials(self, num, password):
        """Validates employeeNumber and password. Returns employee data on success, else None."""
        query_hash = "SELECT hashedPassword FROM employee_auth WHERE employeeNumber = %s"
        auth_data = self.execute_query(query_hash, (num,), fetchone=True)
        
        if auth_data and check_password_hash(auth_data['hashedPassword'], password):
            query_employee = "SELECT * FROM employees WHERE employeeNumber = %s"
            return self.execute_query(query_employee, (num,), fetchone=True)
            
        return None

    def get_assigned_customers(self, employee_number,search="", sort="none"):
        """Fetches all customers for a specific Sales Rep."""
        
        query = """
        SELECT c.customerNumber, c.customerName, c.city, c.country,
               c.salesRepEmployeeNumber,
               IFNULL(SUM(p.amount), 0) AS totalSpend
        FROM customers c
        LEFT JOIN payments p ON c.customerNumber = p.customerNumber
        WHERE c.salesRepEmployeeNumber = %s
          AND c.customerName LIKE %s
        GROUP BY c.customerNumber
        """

        if sort == "asc":
            query += " ORDER BY totalSpend ASC"
        elif sort == "desc":
            query += " ORDER BY totalSpend DESC"
    
        return self.execute_query(query, (employee_number,  (f"%{search}%")))
    
    def get_customer_details(self, customer_number):
        """Fetches all details for a single customer."""
        query = "SELECT * FROM customers WHERE customerNumber = %s"
        return self.execute_query(query, (customer_number,), fetchone=True)

    def get_customer_orders(self, customer_number, sort_by='newest'):
        """
        Fetches orders with sorting.
        sort_by: 'newest' (default) or 'oldest'
        Uses orderNumber as a tie-breaker for same-day orders.
        """
        query = "SELECT * FROM orders WHERE customerNumber = %s"
        
        if sort_by == 'oldest':
            query += " ORDER BY orderDate ASC, orderNumber ASC"
        else:
            query += " ORDER BY orderDate DESC, orderNumber DESC"

        return self.execute_query(query, (customer_number,))

    def get_single_product(self, product_code):
        """Gets a single product by its code."""
        query = "SELECT * FROM products WHERE productCode = %s"
        return self.execute_query(query, (product_code,), fetchone=True)

    def get_all_offices(self):
        """Fetches all office locations."""
        query = "SELECT * FROM offices ORDER BY country, city"
        return self.execute_query(query)
    
    def insert_product(self, product_info):
        """
        Inserts a new product into the products table.

        product_info: tuple in the order:
        (
            productCode, productName, productLine, productScale,
            productVendor, productDescription,
            quantityInStock, buyPrice, MSRP
        )
        """
        query = """
            INSERT INTO products (
                productCode, productName, productLine, productScale,
                productVendor, productDescription,
                quantityInStock, buyPrice, MSRP
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, product_info)
    

    def update_product(self, product_code, product_name, product_line,
                       product_scale, product_vendor, product_description,
                       quantity_in_stock, buy_price, msrp):
        """
        Updates an existing product identified by productCode.
        Returns the number of affected rows (0 if productCode doesn't exist).
        """
        query = """
            UPDATE products
            SET
                productName = %s,
                productLine = %s,
                productScale = %s,
                productVendor = %s,
                productDescription = %s,
                quantityInStock = %s,
                buyPrice = %s,
                MSRP = %s
            WHERE productCode = %s
        """
        params = (
            product_name, product_line, product_scale,
            product_vendor, product_description,
            quantity_in_stock, buy_price, msrp,
            product_code
        )
        return self.execute_query(query, params)

    
    def delete_product(self, product_code):
        """
        Deletes a product by productCode.
        Returns the number of affected rows (0 if productCode doesn't exist).
        """
        query = "DELETE FROM products WHERE productCode = %s"
        return self.execute_query(query, (product_code,))
    
    def execute_query(self, query, params=None, fetchone=False):
        """
        Executes a given query.
        Returns: Fetched rows for SELECT or row count for INSERT/UPDATE/DELETE.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if query.strip().lower().startswith("select"):
                if not fetchone:
                    result = self.cursor.fetchall()
                else:
                    result = self.cursor.fetchone()
                return result 
            else:
                self.db.commit() 
                return self.cursor.rowcount
        
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None

    def get_order(self, order_number):
        """Gets a single order by its number."""
        query = "SELECT * FROM orders WHERE orderNumber = %s"
        return self.execute_query(query, (order_number,), fetchone=True)

    def get_order_details(self, order_number):
        """Gets all items (products) for a specific order."""
        query = """
            SELECT od.*, p.productName
            FROM orderdetails od
            JOIN products p ON od.productCode = p.productCode
            WHERE od.orderNumber = %s
        """
        return self.execute_query(query, (order_number,))
    
    def get_customer_payments(self, customer_number):
        """Returns all payments made by the customer."""
        query = """
            SELECT * FROM payments
            WHERE customerNumber = %s
            ORDER BY paymentDate DESC
        """
        return self.execute_query(query, (customer_number,))

    def get_customer_balance(self, customer_number):
        """Calculates total orders, payments, and balance for a customer."""
        query = """
            SELECT
                IFNULL((
                    SELECT SUM(od.quantityOrdered * od.priceEach)
                    FROM orders o
                    JOIN orderdetails od ON o.orderNumber = od.orderNumber
                    WHERE o.customerNumber = %s
                    AND o.status != 'Cancelled'
                ), 0) AS total_orders,
                IFNULL((
                    SELECT SUM(amount)
                    FROM payments
                    WHERE customerNumber = %s
                ), 0) AS total_payments
        """
        
        result = self.execute_query(query, (customer_number, customer_number), fetchone=True)

        total_orders = Decimal(str(result["total_orders"]))
        total_payments = Decimal(str(result["total_payments"]))
        result["balance"] = total_orders - total_payments
        return result
    
    def feel_lucky(self):
        query = """
                SELECT
                    COALESCE(o.city, off.city) AS city_to_visit,
                    p.productName AS product_to_buy,
                    p.productCode,
                    CAST(FLOOR(RAND() * 100) AS SIGNED) + 1 AS lucky_number
                FROM customers c

                LEFT JOIN employees e
                    ON c.salesRepEmployeeNumber = e.employeeNumber

                LEFT JOIN offices o
                    ON e.officeCode = o.officeCode

                JOIN orders ord
                    ON c.customerNumber = ord.customerNumber

                JOIN orderdetails od
                    ON ord.orderNumber = od.orderNumber

                JOIN products p
                    ON od.productCode = p.productCode

                JOIN (
                    SELECT city
                    FROM offices
                    ORDER BY RAND()
                    LIMIT 1
                ) off

                WHERE ord.orderNumber = (
                    SELECT orderNumber
                    FROM orders
                    ORDER BY RAND()
                    LIMIT 1
                )

                GROUP BY
                    o.city,
                    off.city,
                    p.productName,
                    p.productCode

                ORDER BY RAND()
                LIMIT 1;


        """
        return self.execute_query(query)
    
    def get_all_product_lines(self):
        return self.execute_query("SELECT productLine FROM productlines")

    def get_complex_payment_report(self, city_filter=None, year_filter=None, product_line_filter=None):
        params = []
        query = """
            SELECT 
                o.city AS office_city,
                p.productName,
                p.productLine, 
                IFNULL(SUM(od.quantityOrdered * od.priceEach), 0) as total_revenue,
                SUM(od.quantityOrdered) as total_units,
                (SELECT AVG(quantityOrdered * priceEach) FROM orderdetails) as global_avg_revenue
            FROM offices o
            JOIN employees e ON o.officeCode = e.officeCode
            LEFT JOIN customers c ON e.employeeNumber = c.salesRepEmployeeNumber
            LEFT JOIN orders ord ON c.customerNumber = ord.customerNumber
            LEFT JOIN orderdetails od ON ord.orderNumber = od.orderNumber
            LEFT JOIN products p ON od.productCode = p.productCode
            WHERE 1=1
        """
        
        if city_filter:
            query += " AND o.city LIKE %s"
            params.append(f"%{city_filter}%")
            
        if year_filter and year_filter.isdigit():
            query += " AND (YEAR(ord.orderDate) = %s OR ord.orderDate IS NULL)"
            params.append(year_filter)

        if product_line_filter:
            query += " AND p.productLine = %s"
            params.append(product_line_filter)
            
        query += """
            GROUP BY o.city, p.productName, p.productLine
            ORDER BY total_revenue DESC
            LIMIT 100
        """
        
        return self.execute_query(query, tuple(params))

    def create_customer_auth(self, customer_number, hashed_password):
        """Inserts a new password record into 'customer_auth'."""
        query = "INSERT INTO customer_auth (customerNumber, hashedPassword) VALUES (%s, %s)"
        return self.execute_query(query, (customer_number, hashed_password))

    def create_employee_auth(self, employee_number, hashed_password):
        """Inserts a new password record into 'employee_auth'."""
        query = "INSERT INTO employee_auth (employeeNumber, hashedPassword) VALUES (%s, %s)"
        return self.execute_query(query, (employee_number, hashed_password))

    def create_report(self, employee_number, content):
        """Creates a new report for an employee."""
        query = "INSERT INTO employee_reports (employeeNumber, reportContent) VALUES (%s, %s)"
        return self.execute_query(query, (employee_number, content))

    def get_employee_reports(self, employee_number):
        """Fetches all reports submitted by a specific employee."""
        query = "SELECT * FROM employee_reports WHERE employeeNumber = %s ORDER BY reportDate DESC"
        return self.execute_query(query, (employee_number,))

    def get_subordinate_reports(self, manager_number):
        """Fetches reports from all employees who report to this manager."""
        query = """
            SELECT r.*, e.firstName, e.lastName, e.jobTitle
            FROM employee_reports r
            JOIN employees e ON r.employeeNumber = e.employeeNumber
            WHERE e.reportsTo = %s
            ORDER BY r.reportDate DESC
        """
        return self.execute_query(query, (manager_number,))

    def get_employee_details(self, employee_number):
        """Fetches full details for a specific employee."""
        query = "SELECT * FROM employees WHERE employeeNumber = %s"
        return self.execute_query(query, (employee_number,), fetchone=True)

    def get_subordinates(self, manager_number):
        """Fetches all employees who report to the given manager, including office city."""
        query = """
            SELECT e.employeeNumber, e.firstName, e.lastName, e.email, e.jobTitle, o.city
            FROM employees e
            JOIN offices o ON e.officeCode = o.officeCode
            WHERE e.reportsTo = %s
            ORDER BY e.lastName, e.firstName
        """
        return self.execute_query(query, (manager_number,))
    
    def insert_customer(self, customer_info):
        """
            insert new customer to customers table
        """

        query = """
            INSERT INTO customers (
                customerNumber, customerName, contactLastName, contactFirstName,
                phone, addressLine1, city, country, creditLimit
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NULL)
        """

        return self.execute_query(query,customer_info)

    def insert_customer_to_auth(self, customer_info):
        """
            insert new customer info to customer auth
        """
        query = "INSERT INTO customer_auth (customerNumber, hashedPassword) VALUES(%s, %s)"
        return self.execute_query(query, customer_info)

    def fire_sales_rep(self, employee_id):
        """
        Fires a Sales Rep and reassigns their customers to another Rep in the same office.
        Returns (Success: bool, Message: str).
        """
        try:
            # 1. Validate Employee
            emp = self.get_employee_details(employee_id)
            if not emp:
                return False, "Employee not found."
            if emp['jobTitle'] != 'Sales Rep':
                return False, "Cannot fire: Employee is not a Sales Rep."

            office_code = emp['officeCode']

            # 2. Find replacement Reps in the same office
            query_others = """
                SELECT employeeNumber FROM employees 
                WHERE jobTitle = 'Sales Rep' 
                AND officeCode = %s 
                AND employeeNumber != %s
            """
            others = self.execute_query(query_others, (office_code, employee_id))
            
            if not others:
                return False, "Cannot fire: Only one Sales Rep in this office."

            # Pick the first available replacement
            new_rep_id = others[0]['employeeNumber']

            # 3. Start Transaction
            if self.db.is_connected():
                self.cursor.fetchall() # Clear any unread results
            self.db.autocommit = False

            # 4. Reassign Customers
            query_reassign = "UPDATE customers SET salesRepEmployeeNumber = %s WHERE salesRepEmployeeNumber = %s"
            self.cursor.execute(query_reassign, (new_rep_id, employee_id))

            # 5. Delete Employee Records
            self.cursor.execute("DELETE FROM employee_auth WHERE employeeNumber = %s", (employee_id,))
            self.cursor.execute("DELETE FROM employee_reports WHERE employeeNumber = %s", (employee_id,))
            self.cursor.execute("DELETE FROM employees WHERE employeeNumber = %s", (employee_id,))

            self.db.commit()
            return True, f"Employee fired. Customers reassigned to Rep #{new_rep_id}."

        except mysql.connector.Error as err:
            self.db.rollback()
            print(f"Error firing employee: {err}")
            return False, f"Database error: {err}"
        finally:
            self.db.autocommit = True

    def delete_customer_transaction(self, customer_number):
        """
        Deletes a customer and all associated data (orders, payments, auth) atomically.
        Manages autocommit manually to prevent 'Transaction already in progress' errors.
        """
        try:
            # Ensure no unread results exist on the connection
            if self.db.is_connected():
                self.cursor.fetchall() 
            
            # Disable autocommit to start a manual transaction block
            self.db.autocommit = False

            # --- CASCADE DELETE OPERATIONS ---

            # 1. Fetch customer's orders to target OrderDetails
            query_get_orders = "SELECT orderNumber FROM orders WHERE customerNumber = %s"
            self.cursor.execute(query_get_orders, (customer_number,))
            orders = self.cursor.fetchall()

            # 2. Delete OrderDetails for each order
            if orders:
                for order in orders:
                    query_del_details = "DELETE FROM orderdetails WHERE orderNumber = %s"
                    self.cursor.execute(query_del_details, (order['orderNumber'],))

            # 3. Delete Orders
            query_delete_orders = "DELETE FROM orders WHERE customerNumber = %s"
            self.cursor.execute(query_delete_orders, (customer_number,))

            # 4. Delete Payments
            query_delete_payments = "DELETE FROM payments WHERE customerNumber = %s"
            self.cursor.execute(query_delete_payments, (customer_number,))

            # 5. Delete Customer Authentication (Password/Login)
            query_delete_auth = "DELETE FROM customer_auth WHERE customerNumber = %s"
            self.cursor.execute(query_delete_auth, (customer_number,))

            # 6. Delete Customer Profile
            query_delete_customer = "DELETE FROM customers WHERE customerNumber = %s"
            self.cursor.execute(query_delete_customer, (customer_number,))

            # --- COMMIT TRANSACTION ---
            self.db.commit()
            print(f"SUCCESS: Customer {customer_number} deleted completely.")
            return True

        except mysql.connector.Error as err:
            print(f"Error deleting account: {err}")
            self.db.rollback()
            return False
            
        finally:
            # Restore autocommit to default state for subsequent operations
            self.db.autocommit = True

    def update_customer_profile(self, customer_number, first_name, last_name, phone, address, city, country):
        """
        Updates the profile details of a customer.
        """
        query = """
            UPDATE customers 
            SET contactFirstName = %s, 
                contactLastName = %s, 
                phone = %s, 
                addressLine1 = %s, 
                city = %s, 
                country = %s
            WHERE customerNumber = %s
        """
        # Send datas as a tuples
        params = (first_name, last_name, phone, address, city, country, customer_number)
        return self.execute_query(query, params)

    def get_all_offices(self):
        """
        Fetches all offices. 
        UPDATED: Now includes the count of employees in each office.
        """
        query = """
            SELECT o.*, 
            (SELECT COUNT(*) FROM employees e WHERE e.officeCode = o.officeCode) as employee_count
            FROM offices o
            ORDER BY o.country, o.city
        """
        return self.execute_query(query)

    def get_office_by_code(self, office_code):
        """Fetches a single office by code."""
        query = "SELECT * FROM offices WHERE officeCode = %s"
        return self.execute_query(query, (office_code,), fetchone=True)

    def insert_office(self, office_data):
        """
        Inserts a new office.
        office_data tuple: (officeCode, city, phone, address1, address2, state, country, postalCode, territory)
        """
        query = """
            INSERT INTO offices 
            (officeCode, city, phone, addressLine1, addressLine2, state, country, postalCode, territory)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, office_data)

    def update_office(self, office_code, phone, address1, address2, state, postal_code, territory):
        """
        Updates editable office details. 
        Note: City and Country are typically fixed for an office location ID, 
        but address/phone can change.
        """
        query = """
            UPDATE offices 
            SET phone = %s, 
                addressLine1 = %s, 
                addressLine2 = %s, 
                state = %s, 
                postalCode = %s, 
                territory = %s
            WHERE officeCode = %s
        """
        params = (phone, address1, address2, state, postal_code, territory, office_code)
        return self.execute_query(query, params)

    def delete_office(self, office_code):
        """
        Deletes an office ONLY IF it has no employees.
        Returns: (Success: bool, Message: str)
        """
        # 1. Check for employees
        check_query = "SELECT COUNT(*) as count FROM employees WHERE officeCode = %s"
        result = self.execute_query(check_query, (office_code,), fetchone=True)
        
        if result and result['count'] > 0:
            return False, f"Cannot delete office. It has {result['count']} employees assigned."

        # 2. Delete if safe
        del_query = "DELETE FROM offices WHERE officeCode = %s"
        rows = self.execute_query(del_query, (office_code,))
        
        if rows:
            return True, "Office deleted successfully."
        else:
            return False, "Error deleting office or office not found."
        
    def sort_popular_products(self, product_line):
        query = """
                SELECT p.*, COALESCE(SUM(od.quantityOrdered),0) AS popularity
                FROM products p
                LEFT JOIN orderdetails od ON p.productCode = od.productCode
                WHERE p.productLine = %s
                GROUP BY p.productCode
                ORDER BY popularity DESC;
                    """
        return self.execute_query(query,(product_line,))


    def delete_order_item(self, detail_id):
        """Removes a single line item from an order."""
        query = "DELETE FROM orderdetails WHERE orderDetailsNumber = %s"
        return self.execute_query(query, (detail_id,))

    def get_order_detail_by_id(self, detail_id):
        """Fetches a single order detail row. Needed for security checks."""
        query = "SELECT * FROM orderdetails WHERE orderDetailsNumber = %s"
        return self.execute_query(query, (detail_id,), fetchone=True)

    def create_payment(self, customer_number, check_number, amount):
        """Inserts a new payment record for a customer."""
        # paymentDate is set to the current date/time using NOW()
        query = "INSERT INTO payments (customerNumber, checkNumber, paymentDate, amount) VALUES (%s, %s, NOW(), %s)"
        # The parameters match the query placeholders: (customer_number, check_number, amount)
        return self.execute_query(query, (customer_number, check_number, amount))

    def delete_payment(self, customer_number, check_number):
        """Deletes a specific payment record."""
        query = "DELETE FROM payments WHERE customerNumber = %s AND checkNumber = %s"
        return self.execute_query(query, (customer_number, check_number))

    def update_payment_check_number(self, customer_number, old_check_number, new_check_number):
        """Updates the check number for a payment (e.g., to fix a typo)."""
        query = "UPDATE payments SET checkNumber = %s WHERE customerNumber = %s AND checkNumber = %s"
        return self.execute_query(query, (new_check_number, customer_number, old_check_number))

    def get_payment_details(self, customer_number, check_number):
        """Fetches a single payment record for editing."""
        query = "SELECT * FROM payments WHERE customerNumber = %s AND checkNumber = %s"
        return self.execute_query(query, (customer_number, check_number), fetchone=True)

    def update_payment(self, customer_number, old_check_number, new_check_number, new_amount):
        """Updates a payment's check number and amount."""
        query = """
            UPDATE payments 
            SET checkNumber = %s, amount = %s 
            WHERE customerNumber = %s AND checkNumber = %s
        """
        return self.execute_query(query, (new_check_number, new_amount, customer_number, old_check_number))

    def get_all_customers_with_balance(self, search="", sort="none"):
        """Fetches all customers for the manager view."""
        query = """
        SELECT c.customerNumber, c.customerName, c.city, c.country, 
               c.salesRepEmployeeNumber,
               IFNULL(SUM(p.amount), 0) AS totalSpend
        FROM customers c
        LEFT JOIN payments p ON c.customerNumber = p.customerNumber
        WHERE c.customerName LIKE %s
        GROUP BY c.customerNumber
        """

        # Sorting
        if sort == "asc":
            query += " ORDER BY totalSpend ASC"
        elif sort == "desc":
            query += " ORDER BY totalSpend DESC"
            
        customers = self.execute_query(query, (f"%{search}%",))
        
        results = []
        for c in customers:
            bal_data = self.get_customer_balance(c['customerNumber'])
            c['balance'] = bal_data['balance']
            results.append(c)
            
        return results    

    def update_order_item_quantity(self, detail_id, new_quantity):
        """Updates the quantity of a specific order line item."""
        query = "UPDATE orderdetails SET quantityOrdered = %s WHERE orderDetailsNumber = %s"
        return self.execute_query(query, (new_quantity, detail_id))

    def get_next_employee_number(self):
        """Returns the next available employee number."""
        query = "SELECT MAX(employeeNumber) as max_id FROM employees"
        result = self.execute_query(query, fetchone=True)
        if result and result['max_id']:
            return result['max_id'] + 1
        return 1001 # Default start if table is empty

    def add_employee(self, employee_number, last_name, first_name, extension, email, office_code, reports_to, job_title):
        """Inserts a new employee record."""
        query = """
            INSERT INTO employees (employeeNumber, lastName, firstName, extension, email, officeCode, reportsTo, jobTitle)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (employee_number, last_name, first_name, extension, email, office_code, reports_to, job_title)
        return self.execute_query(query, params)

    def get_office_order_stats(self):
        """
        Retreives stats per office including Total Sales Volume using a NESTED QUERY.
        Structure: Office -> Employees -> Customers -> Orders -> OrderDetails
        """
        query = """
            SELECT 
                o.officeCode,
                o.city,
                o.country,
                (SELECT COUNT(*) 
                 FROM orders ord
                 JOIN customers c ON ord.customerNumber = c.customerNumber
                 JOIN employees e ON c.salesRepEmployeeNumber = e.employeeNumber
                 WHERE e.officeCode = o.officeCode
                ) as total_orders,
                
                (SELECT MAX(ord.orderDate)
                 FROM orders ord
                 JOIN customers c ON ord.customerNumber = c.customerNumber
                 JOIN employees e ON c.salesRepEmployeeNumber = e.employeeNumber
                 WHERE e.officeCode = o.officeCode
                ) as last_activity,

                COALESCE(
                    (SELECT SUM(od.quantityOrdered * od.priceEach)
                     FROM orderdetails od
                     JOIN orders ord ON od.orderNumber = ord.orderNumber
                     JOIN customers c ON ord.customerNumber = c.customerNumber
                     JOIN employees e ON c.salesRepEmployeeNumber = e.employeeNumber
                     WHERE e.officeCode = o.officeCode
                    ), 0
                ) as total_sales
            FROM offices o
            ORDER BY total_sales DESC
        """
        return self.execute_query(query)

    def get_offices_activity_report(self):
        """
        Retrieves workforce activity.
        Fixes: Fetches Territory, Active Counts, and Manager Names correctly using Subqueries.
        """
        query = """
            SELECT 
                o.city,
                o.territory, -- Territory verisini buradan çekiyoruz
                
                (SELECT COUNT(*) 
                 FROM employees e 
                 WHERE e.officeCode = o.officeCode
                ) as active_employees,

                (SELECT COUNT(*)
                 FROM customers c
                 JOIN employees e ON c.salesRepEmployeeNumber = e.employeeNumber
                 WHERE e.officeCode = o.officeCode
                ) as customer_count,

                COALESCE(
                    (SELECT CONCAT(firstName, ' ', lastName)
                     FROM employees e
                     WHERE e.officeCode = o.officeCode 
                     AND (jobTitle LIKE '%Manager%' OR jobTitle LIKE '%VP%' OR jobTitle LIKE '%President%')
                     LIMIT 1
                    ), 'Regional Lead'
                ) as managers
                
            FROM offices o
            ORDER BY active_employees DESC
        """
        return self.execute_query(query)

    def create_order_transaction(self, customer_number, cart_items, comment=""):
        """
        Creates an order and its details atomically.
        """
        try:
            if self.db.is_connected():
                self.cursor.fetchall()
            
            self.db.autocommit = False

            self.cursor.execute("SELECT MAX(orderNumber) AS maxNum FROM orders")
            res = self.cursor.fetchone()
            next_order_id = (res["maxNum"] or 0) + 1

            # If empty comment, set default 
            final_comment = comment if comment else "Web Order"

            query_order = """
                INSERT INTO orders (orderNumber, orderDate, requiredDate, status, comments, customerNumber)
                VALUES (%s, NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY), 'In Process', %s, %s)
            """
            self.cursor.execute(query_order, (next_order_id, final_comment, customer_number))

            query_detail = """
                INSERT INTO orderdetails (orderNumber, productCode, quantityOrdered, priceEach, orderLineNumber)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            line_number = 1
            for code, item in cart_items.items():
                self.cursor.execute(query_detail, (
                    next_order_id, 
                    code, 
                    item["quantity"], 
                    item["priceEach"], 
                    line_number
                ))
                line_number += 1

            self.db.commit()
            return True, next_order_id

        except Exception as e:
            self.db.rollback()
            print(f"Transaction Error: {e}")
            return False, str(e)
            
        finally:
            self.db.autocommit = True

    def update_order_comment(self, order_number, new_comment):
        """Updates the comment/notes of a specific order."""
        query = "UPDATE orders SET comments = %s WHERE orderNumber = %s"
        return self.execute_query(query, (new_comment, order_number))

    def delete_order_permanently(self, order_number):
        """
        Hard Deletes an order. 
        Database 'ON DELETE CASCADE' will automatically remove related orderdetails.
        """
        try:
            query = "DELETE FROM orders WHERE orderNumber = %s"
            
            row_count = self.execute_query(query, (order_number,))
            
            if row_count and row_count > 0:
                return True, f"Order #{order_number} permanently deleted."
            else:
                return False, "Order not found or could not be deleted."

        except mysql.connector.Error as err:
            return False, f"Database Error: {err}"

    def get_employee_performance_matrix(self, limit=10, offset=0):
        """
        Complex Join (Employees -> Customers -> Orders -> OrderDetails -> Products) + Group By
        Supports pagination.
        """
        query = """
            SELECT 
                e.firstName, 
                e.lastName, 
                p.productLine, 
                SUM(od.quantityOrdered * od.priceEach) as revenue
            FROM employees e
            JOIN customers c ON e.employeeNumber = c.salesRepEmployeeNumber
            JOIN orders o ON c.customerNumber = o.customerNumber
            JOIN orderdetails od ON o.orderNumber = od.orderNumber
            JOIN products p ON od.productCode = p.productCode
            WHERE e.jobTitle = 'Sales Rep'
            GROUP BY e.employeeNumber, e.firstName, e.lastName, p.productLine
            ORDER BY e.employeeNumber
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, (limit, offset))

    def get_unproductive_employees(self):
        """
        Outer Join (Employees left join Customers left join Orders)
        Starts STRICTLY from 'employees' table.
        Identifies Sales Reps with NO orders (or no customers).
        """
        query = """
            SELECT 
                e.employeeNumber, 
                e.firstName, 
                e.lastName, 
                e.email, 
                e.jobTitle,
                COUNT(c.customerNumber) as customer_count,
                COUNT(o.orderNumber) as order_count
            FROM employees e
            LEFT JOIN customers c ON e.employeeNumber = c.salesRepEmployeeNumber
            LEFT JOIN orders o ON c.customerNumber = o.customerNumber
            WHERE e.jobTitle = 'Sales Rep'
            GROUP BY e.employeeNumber, e.firstName, e.lastName, e.email, e.jobTitle
            HAVING order_count = 0
        """
        return self.execute_query(query)

    def get_filtered_orders(self, customer_number, filters):
        """
        Advanced Filtering with Dynamic SQL & Nested Queries.
        Satisfies 'Nested Query' requirement for Price and Category filtering.
        """
    
        query = "SELECT * FROM orders WHERE customerNumber = %s"
        params = [customer_number]

        # status filter
        if filters.get('status'):
            placeholders = ', '.join(['%s'] * len(filters['status']))
            query += f" AND status IN ({placeholders})"
            params.extend(filters['status'])

        # category filter
        if filters.get('categories'):
            cat_placeholders = ', '.join(['%s'] * len(filters['categories']))
            query += f"""
                AND orderNumber IN (
                    SELECT orderNumber 
                    FROM orderdetails 
                    WHERE productCode IN (
                        SELECT productCode 
                        FROM products 
                        WHERE productLine IN ({cat_placeholders})
                    )
                )
            """
            params.extend(filters['categories'])

        # price range filter
        if filters.get('price_ranges'):
            price_conditions = []
            
            for rng in filters['price_ranges']:
                if rng == '0-1000':
                    price_conditions.append("SUM(quantityOrdered * priceEach) BETWEEN 0 AND 1000")
                elif rng == '1000-10000':
                    price_conditions.append("SUM(quantityOrdered * priceEach) BETWEEN 1000 AND 10000")
                elif rng == '10000-50000':
                    price_conditions.append("SUM(quantityOrdered * priceEach) BETWEEN 10000 AND 50000")
                elif rng == '50000-100000':
                    price_conditions.append("SUM(quantityOrdered * priceEach) BETWEEN 50000 AND 100000")
                elif rng == '100000+':
                    price_conditions.append("SUM(quantityOrdered * priceEach) > 100000")
            
            if price_conditions:
                or_clause = " OR ".join(price_conditions)
                query += f"""
                    AND orderNumber IN (
                        SELECT orderNumber 
                        FROM orderdetails 
                        GROUP BY orderNumber 
                        HAVING {or_clause}
                    )
                """
        # sort by date
        sort_order = filters.get('sort_date', 'newest')
        if sort_order == 'oldest':
            query += " ORDER BY orderDate ASC, orderNumber ASC"
        else:
            query += " ORDER BY orderDate DESC, orderNumber DESC"

        return self.execute_query(query, tuple(params))

    def close(self):
        """Closes the cursor and database connection."""
        self.cursor.close()
        self.db.close()
