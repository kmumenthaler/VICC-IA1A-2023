from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, current_user
import mysql.connector
from datetime import datetime
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = './static/books/'

app = Flask(__name__)
app.config['SECRET_KEY'] = '1576bfab8ae6bda607dd03c271afe64a'

# Datenbank-Verbindungsinformationen
db_config = {
    'host': 'db',
    'user': 'root',
    'password': 'Start123.',
    'database': 'BuchrezensionsPlattform'
}

# Datenbankverbindung
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/books')
def books():
    cursor.execute("SELECT * FROM Bücher")
    buecher = cursor.fetchall()

    # Füge die durchschnittliche Bewertung zu jedem Buch hinzu
    for buch in buecher:
        cursor.execute("SELECT AVG(Bewertung) as Durchschnitt FROM Bewertungen WHERE BuchID = %s", (buch['BuchID'],))
        bewertung = cursor.fetchone()
        buch['DurchschnittlicheBewertung'] = int(bewertung['Durchschnitt'] if bewertung['Durchschnitt'] else 0)

    return render_template('books.html', buecher=buecher)

@app.route('/book/<int:book_id>', methods=['GET'])
def book_detail(book_id):
    cursor.execute("SELECT * FROM Bücher WHERE BuchID = %s", (book_id,))
    buch = cursor.fetchone()
    cursor.execute("SELECT b.Bewertung, b.Kommentar, u.Benutzername FROM Bewertungen b INNER JOIN Benutzer u ON b.UserID = u.UserID WHERE b.BuchID = %s", (book_id,))
    bewertungen = cursor.fetchall()
    kommentare = bewertungen
    bewertung_werte = [bewertung['Bewertung'] for bewertung in bewertungen]
    durchschnittliche_bewertung = int(round(sum(bewertung_werte) / len(bewertung_werte))) if bewertung_werte else None
    hat_bewertet = hat_bewertung_abgegeben(session['userID'], book_id)
    return render_template('book_detail.html', buch=buch, durchschnittliche_bewertung=durchschnittliche_bewertung, kommentare=kommentare, hat_bewertung_abgegeben=hat_bewertet, bewertungen=bewertungen)

@app.route('/buch/<int:buch_id>/bewertung_abgeben', methods=['GET', 'POST'])
def bewertung_abgeben(buch_id):
    if 'logged_in' not in session:
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))
    if hat_bewertung_abgegeben(session['userID'], buch_id):
        flash('Sie haben bereits eine Bewertung für dieses Buch abgegeben.')
        return redirect(url_for('book_detail', book_id=buch_id))
    if request.method == 'POST':
        bewertung = request.form.get('bewertung')
        kommentar = request.form.get('kommentar')
        current_date = datetime.now().date()
        try:
            cursor.execute(
                "INSERT INTO Bewertungen (BuchID, UserID, Bewertung, Kommentar, Datum) VALUES (%s, %s, %s, %s, %s)",
                (buch_id, session.get('userID'), bewertung, kommentar, current_date)
            )
            conn.commit()
            flash('Ihre Bewertung wurde erfolgreich abgegeben!')
        except Exception as e:
            conn.rollback()
            flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')
            print(e)
        return redirect(url_for('book_detail', book_id=buch_id))
    buch = get_buch_info(buch_id)
    return render_template('bewertung_abgeben.html', buch=buch)

def get_buch_info(buch_id):
    cursor.execute("SELECT * FROM Bücher WHERE BuchID = %s", (buch_id,))
    buch = cursor.fetchone()
    return buch

def hat_bewertung_abgegeben(user_id, buch_id):
    cursor.execute("SELECT * FROM Bewertungen WHERE UserID = %s AND BuchID = %s", (user_id, buch_id))
    bewertung = cursor.fetchone()
    return bool(bewertung)

@app.route('/reviews')
def reviews():
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
        current_date = datetime.now().date()
        try:
            cursor.execute(
                "INSERT INTO Benutzer (Benutzername, Email, Passwort, Registrierungsdatum) VALUES (%s, %s, %s, %s)",
                (username, email, password, current_date)
            )
            conn.commit()
            flash('Erfolgreich registriert!')
            return redirect(url_for('home'))
        except Exception as e:
            conn.rollback()
            flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')
            print(e)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cursor.execute(
            "SELECT Passwort, UserID FROM Benutzer WHERE Benutzername=%s", (username,)
        )
        result = cursor.fetchone()
        if result and result['Passwort'] == password:
            session['logged_in'] = True
            session['username'] = username
            session['userID'] = result['UserID']
            flash('Erfolgreich angemeldet!')
            return redirect(url_for('home'))
        else:
            flash('Falscher Benutzername oder Passwort!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Erfolgreich abgemeldet!')
    return redirect(url_for('home'))

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'logged_in' not in session:
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        file = request.files.get('book_img')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            img_path = os.path.join(UPLOAD_FOLDER, filename)
            current_date = datetime.now().date()
            try:
                cursor.execute(
                    "INSERT INTO Bücher (Titel, Autor, Beschreibung, Bildpfad, Eingabedatum) VALUES (%s, %s, %s, %s, %s)",
                    (title, author, description, img_path, current_date)
                )
                conn.commit()
                flash('Buch erfolgreich hinzugefügt!')
            except Exception as e:
                conn.rollback()
                flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')
                print(e)
            return redirect(url_for('books'))
    return render_template('add_book.html')

@app.route('/profile', methods=['GET'])
def profile():
    if 'logged_in' not in session:
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))

    user_id = session.get('userID')
    cursor.execute("SELECT * FROM Benutzer WHERE UserID = %s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("""
    SELECT b.*, br.Bewertung, br.Kommentar, br.Datum 
    FROM Bewertungen br
    INNER JOIN Bücher b ON b.BuchID = br.BuchID
    WHERE br.UserID = %s
    """, (user_id,))
    user_reviews = cursor.fetchall()

    total_reviews = len(user_reviews)
    avg_rating = round(sum([r['Bewertung'] for r in user_reviews]) / total_reviews, 2) if user_reviews else None

    return render_template('profile.html', user=user, user_reviews=user_reviews, total_reviews=total_reviews, avg_rating=avg_rating)

if __name__ == '__main__':
    app.run(debug=True)