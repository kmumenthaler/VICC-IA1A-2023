from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# Datenbank-Verbindungsinformationen
db_config = {
    'host': 'db',  # Docker-Service-Name für MariaDB
    'user': 'root',
    'password': 'Start123.',
    'database': 'BuchrezensionsPlattform'
}

# Datenbankverbindung
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/books')
def books():
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    # Ausgabe als Beispielliste für den Moment; Sie können die tatsächlichen Daten aus Ihrer DB abrufen und anzeigen
    return render_template('books.html', tables=tables)


@app.route('/reviews')
def reviews():
    # Beispielliste; Sie können die tatsächlichen Daten aus Ihrer DB abrufen und anzeigen
    reviews = ["Review 1", "Review 2", "Review 3"]
    return render_template('reviews.html', reviews=reviews)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
