from flask import Flask
from db_helper import DatabaseHandler
from os import getenv
from dotenv import load_dotenv

# Import route modules
from routes.auth import init_auth_routes
from routes.main import init_main_routes
from routes.cart import init_cart_routes
from routes.orders import init_order_routes
from routes.customer import init_customer_routes
from routes.employee import init_employee_routes
from routes.products import init_product_routes
from routes.offices import init_office_routes

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Get password from environment variable
db_password = getenv("DB_PASSWORD")

if not db_password:
    raise ValueError("DB_PASSWORD environment variable not set. Please create a .env file.")

db = DatabaseHandler(password=db_password)

# Initialize all routes with the app and database instance
init_auth_routes(app, db)
init_main_routes(app, db)
init_cart_routes(app, db)
init_order_routes(app, db)
init_customer_routes(app, db)
init_employee_routes(app, db)
init_product_routes(app, db)
init_office_routes(app, db)

if __name__ == '__main__':
    app.run(debug=False)
