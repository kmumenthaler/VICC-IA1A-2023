from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '1576bfab8ae6bda607dd03c271afe64a'

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Die Passwörter stimmen nicht überein.')
            return redirect('/register')
        
        # Aktuelles Datum holen
        current_date = datetime.now().date()
        
        # Verbindung zur Datenbank und Einfügung des Benutzers
        try:
            cursor.execute(
                "INSERT INTO Benutzer (Benutzername, Email, Passwort, Registrierungsdatum) VALUES (%s, %s, %s, %s)", 
                (username, email, password, current_date)
            )
            conn.commit()
            flash('Erfolgreich registriert!')
            return redirect(url_for('home'))  # Nach erfolgreicher Registrierung können Sie den Benutzer zur Startseite weiterleiten.
        
        except Exception as e:
            conn.rollback()
            flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')
            print(e)  # Für Debugging-Zwecke

    return render_template('register.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
