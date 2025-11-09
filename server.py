from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="", # Enter your SQL password here
    database="classicmodels"
)

@app.route('/')
def index():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT productLine, textDescription FROM productlines")
    productlines = cursor.fetchall()
    return render_template('index.html', productlines=productlines)

if __name__ == '__main__':
    app.run(debug=True)