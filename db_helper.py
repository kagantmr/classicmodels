import mysql.connector
# Import hashing functions
from werkzeug.security import generate_password_hash, check_password_hash

class DatabaseHandler:
    def __init__(self,host="localhost",user="root",password="",database="classicmodels"):
        self.db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.db.cursor(dictionary=True) # returns results as dict

    # UPDATED: Checks credentials against auth table
    def check_customer_credentials(self, num, password):
        """
        Validates customerNumber and password.
        Returns customer data from 'customers' table on success, else None.
        """
        # 1. Get hash from 'customer_auth' table
        query_hash = "SELECT hashedPassword FROM customer_auth WHERE customerNumber = %s"
        auth_data = self.execute_query(query_hash, (num,), fetchone=True)
        
        # 2. Check if auth record exists AND password matches hash
        if auth_data and check_password_hash(auth_data['hashedPassword'], password):
            # 3. On success, fetch main customer data for session
            query_customer = "SELECT * FROM customers WHERE customerNumber = %s"
            return self.execute_query(query_customer, (num,), fetchone=True)
        
        # Invalid credentials or user not found
        return None
    
    # UPDATED: Checks credentials against auth table
    def check_employee_credentials(self, num, password):
        """
        Validates employeeNumber and password.
        Returns employee data from 'employees' table on success, else None.
        """
        # 1. Get hash from 'employee_auth' table
        query_hash = "SELECT hashedPassword FROM employee_auth WHERE employeeNumber = %s"
        auth_data = self.execute_query(query_hash, (num,), fetchone=True)
        
        # 2. Check if auth record exists AND password matches hash
        if auth_data and check_password_hash(auth_data['hashedPassword'], password):
            # 3. On success, fetch main employee data for session
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
    
    def execute_query(self, query, params=None, fetchone=False):
        """
        Executes a given query.
        Returns:
            - Fetched rows for SELECT.
            - Row count for INSERT/UPDATE/DELETE.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            # Handle SELECT queries
            if query.strip().lower().startswith("select"):
                if not fetchone:
                    result = self.cursor.fetchall()
                else:
                    result = self.cursor.fetchone()
                return result 
            # Handle INSERT/UPDATE/DELETE
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

    def get_order_payments(self, order_number):
        """Gets payments associated with an order's customer."""
        query = """
            SELECT p.* FROM payments p
            JOIN orders o ON p.customerNumber = o.customerNumber
            WHERE o.orderNumber = %s
        """
        return self.execute_query(query, (order_number,))
    
    def get_single_product(self, product_code):
        """Gets a single product by its code."""
        query = "SELECT * FROM products WHERE productCode = %s"
        return self.execute_query(query, (product_code,), fetchone=True)
        
    # --- NEW HELPER FUNCTIONS (For password backfill script) ---

    def get_customers_without_auth(self):
        """Finds customers missing an entry in 'customer_auth'."""
        query = """
            SELECT c.customerNumber
            FROM customers c
            LEFT JOIN customer_auth ca ON c.customerNumber = ca.customerNumber
            WHERE ca.hashedPassword IS NULL
        """
        return self.execute_query(query)

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

    def close(self):
        """Closes the cursor and database connection."""
        self.cursor.close()
        self.db.close()