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

    def get_assigned_customers(self, employee_number):
        """Fetches all customers for a specific Sales Rep."""
        query = "SELECT customerNumber, customerName, city, country FROM customers WHERE salesRepEmployeeNumber = %s"
        return self.execute_query(query, (employee_number,))
    
    def get_customer_details(self, customer_number):
        """Fetches all details for a single customer."""
        query = "SELECT * FROM customers WHERE customerNumber = %s"
        return self.execute_query(query, (customer_number,), fetchone=True)

    def get_customer_orders(self, customer_number):
        """Fetches all orders for a specific customer, newest first."""
        query = "SELECT * FROM orders WHERE customerNumber = %s ORDER BY orderDate DESC"
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

    def get_employees_without_auth(self):
        """Finds employees missing an entry in 'employee_auth'."""
        query = """
            SELECT e.employeeNumber
            FROM employees e
            LEFT JOIN employee_auth ea ON e.employeeNumber = ea.employeeNumber
            WHERE ea.hashedPassword IS NULL
        """
        return self.execute_query(query)

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

    def close(self):
        """Closes the cursor and database connection."""
        self.cursor.close()
        self.db.close()
