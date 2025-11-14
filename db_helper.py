import mysql.connector

class DatabaseHandler:
    def __init__(self,host="localhost",user="root",password="",database="classicmodels"):
        self.db = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.db.cursor(dictionary=True) # returns results as dict

    def check_customer_number(self,num):
        """
        check if the customer number exits in customer table
        """
        query = "SELECT * FROM customers WHERE customerNumber = %s"
        self.cursor.execute(query,(num,))
        result = self.cursor.fetchone()
        return result
    
    def check_employee_number(self,num):
        """
        check if the employee number exists in employee table
        """
        query = "SELECT * FROM employees WHERE employeeNumber = %s"
        self.cursor.execute(query,(num,))
        result = self.cursor.fetchone()
        return result

    def get_assigned_customers(self, employee_number):
        """Fetches all customers assigned to a specific Sales Rep."""
        query = "SELECT customerNumber, customerName, city, country FROM customers WHERE salesRepEmployeeNumber = %s"
        self.cursor.execute(query, (employee_number,))
        return self.cursor.fetchall()
    
    def execute_query(self,query, params=None):
        """
        execute the given query
        Returns:
            - For Select: fetched rows
            - For Insert/Update/Delete: number of affected rows
        Raises:
            - mysql.connector.Error if the query fails
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            # if its a select query
            if query.strip().lower().startswith("select"):
                result = self.cursor.fetchall()
                return result 
            else:
                self.db.commit() # commit changes for insert/update/delete
                return self.cursor.rowcount
        
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None
    
    def close(self):
        self.cursor.close()
        self.db.close()
