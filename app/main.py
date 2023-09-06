from database import get_db_connection, get_newest_books, get_popular_books, get_latest_reviews, get_all_books, get_book_details
from utils import compute_average_rating
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, current_user
import mysql.connector
from datetime import datetime
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = './static/books/'

app = Flask(__name__)
app.config['SECRET_KEY'] = '1576bfab8ae6bda607dd03c271afe64a'

@app.route('/')
def home():
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()
    # 5 neueste Bücher
    newest_books_query = "SELECT * FROM Bücher ORDER BY BuchID DESC LIMIT 5"
    newest_books = get_newest_books(cursor)

    # Beliebteste Bücher (wir nehmen hier auch 5)
    popular_books_query = """
    SELECT Bücher.*, AVG(Bewertungen.Bewertung) as avg_rating
    FROM Bücher
    JOIN Bewertungen ON Bücher.BuchID = Bewertungen.BuchID
    GROUP BY Bücher.BuchID
    ORDER BY avg_rating DESC, Bücher.BuchID DESC 
    LIMIT 5
    """
    popular_books = get_popular_books(cursor)

    # Benutzeraktivität: 5 neueste Bewertungen
    latest_reviews_query = """
    SELECT Benutzer.Benutzername, Bücher.Titel, Bewertungen.Bewertung, Bewertungen.Kommentar, Bewertungen.Datum 
    FROM Bewertungen
    JOIN Benutzer ON Bewertungen.UserID = Benutzer.UserID
    JOIN Bücher ON Bewertungen.BuchID = Bücher.BuchID
    ORDER BY Bewertungen.Datum DESC
    LIMIT 5
    """
    latest_reviews = get_latest_reviews(cursor)

    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()

    return render_template('home.html', newest_books=newest_books, popular_books=popular_books, latest_reviews=latest_reviews)

@app.route('/books')
def books():
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

    buecher = get_all_books(cursor)

    # Füge die durchschnittliche Bewertung zu jedem Buch hinzu
    for buch in buecher:
        cursor.execute("SELECT Bewertung FROM Bewertungen WHERE BuchID = %s", (buch['BuchID'],))
        bewertungen = cursor.fetchall()
        ratings = [bewertung['Bewertung'] for bewertung in bewertungen]
        buch['DurchschnittlicheBewertung'] = compute_average_rating(ratings)

    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()

    return render_template('books.html', buecher=buecher)

@app.route('/book/<int:book_id>', methods=['GET'])
def book_detail(book_id):

    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

    buch = get_book_details(cursor, book_id)
    cursor.execute("SELECT b.Bewertung, b.Kommentar, u.Benutzername FROM Bewertungen b INNER JOIN Benutzer u ON b.UserID = u.UserID WHERE b.BuchID = %s", (book_id,))
    bewertungen = cursor.fetchall()
    kommentare = bewertungen
    ratings = [bewertung['Bewertung'] for bewertung in bewertungen]
    durchschnittliche_bewertung = compute_average_rating(ratings)
    cursor.execute("SELECT COUNT(*) FROM Bewertungen WHERE BuchID = %s", (book_id,))
    bewertungs_anzahl = cursor.fetchone()['COUNT(*)']
    
    user_id = session.get('userID')
    hat_bewertet = False
    if user_id:
        hat_bewertet = hat_bewertung_abgegeben(user_id, book_id)
    
    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()

    return render_template('book_detail.html', buch=buch, durchschnittliche_bewertung=durchschnittliche_bewertung, kommentare=kommentare, hat_bewertung_abgegeben=hat_bewertet, bewertungen=bewertungen, bewertungs_anzahl=bewertungs_anzahl)

@app.route('/buch/<int:buch_id>/bewertung_abgeben', methods=['GET', 'POST'])
def bewertung_abgeben(buch_id):
    
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

    if not session.get('logged_in', False):
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))
    
    user_id = session.get('userID')
    if hat_bewertung_abgegeben(user_id, buch_id):  # Die Überprüfung wurde nach dem Login-Check verschoben
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

        # Schließe die Datenbankverbindung am Ende der Route
        cursor.close()
        conn.close()

        return redirect(url_for('book_detail', book_id=buch_id))
    buch = get_buch_info(buch_id)
    return render_template('bewertung_abgeben.html', buch=buch)

def get_buch_info(buch_id):
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

    cursor.execute("SELECT * FROM Bücher WHERE BuchID = %s", (buch_id,))
    buch = cursor.fetchone()

    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()

    return buch

def hat_bewertung_abgegeben(user_id, buch_id):
    # Datenbankverbindung und Cursor erhalten
    conn, _ = get_db_connection()  # Das Unterstrich-Zeichen (_) wird verwendet, um den zurückgegebenen Cursor zu ignorieren
    cursor = conn.cursor(buffered=True)

    cursor.execute("SELECT * FROM Bewertungen WHERE UserID = %s AND BuchID = %s", (user_id, buch_id))
    bewertung = cursor.fetchone()

    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()
    
    return bool(bewertung)

@app.route('/reviews')
def reviews():
    reviews = ["Review 1", "Review 2", "Review 3"]
    return render_template('reviews.html', reviews=reviews)

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

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

            # Schließe die Datenbankverbindung am Ende der Route
            cursor.close()
            conn.close()
            
            return redirect(url_for('home'))
        except Exception as e:
            conn.rollback()
            flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')
            print(e)

            # Schließe die Datenbankverbindung am Ende der Route
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()
    
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

    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Erfolgreich abgemeldet!')
    return redirect(url_for('home'))

@app.route('/add-book', methods=['GET', 'POST'])
def add_book():
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()
    
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
                # Schließe die Datenbankverbindung am Ende der Route
                cursor.close()
                conn.close()
            return redirect(url_for('books'))
        
    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()

    return render_template('add_book.html')

@app.route('/profile', methods=['GET'])
def profile():
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

    if 'logged_in' not in session:
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))

    user_id = session.get('userID')
    cursor.execute("SELECT * FROM Benutzer WHERE UserID = %s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("""
    SELECT b.*, br.BewertungsID, br.Bewertung, br.Kommentar, br.Datum 
    FROM Bewertungen br
    INNER JOIN Bücher b ON b.BuchID = br.BuchID
    WHERE br.UserID = %s
    """, (user_id,))
    user_reviews = cursor.fetchall()

    total_reviews = len(user_reviews)
    avg_rating = round(sum([r['Bewertung'] for r in user_reviews]) / total_reviews, 2) if user_reviews else None

    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()

    return render_template('profile.html', user=user, user_reviews=user_reviews, total_reviews=total_reviews, avg_rating=avg_rating)

@app.route('/delete-profile')
def delete_profile():
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()
    
    # Überprüfe, ob der Benutzer angemeldet ist
    user_id = session.get('userID')
    if not user_id:
        flash('Du musst angemeldet sein, um dein Profil zu löschen.', 'danger')
        return redirect(url_for('login')) # Angenommen, du hast eine 'login'-Route

    # Lösche alle zugehörigen Daten (z.B. Bewertungen) 
    # - Je nach Datenbankdesign könnten dies auch Fremdschlüssel-Beziehungen mit CASCADE-Löschen übernehmen.
    cursor.execute("DELETE FROM Bewertungen WHERE UserID = %s", (user_id,))

    # Lösche den Benutzer
    cursor.execute("DELETE FROM Benutzer WHERE UserID = %s", (user_id,))
    
    # Commit die Änderungen
    conn.commit()

    # Logge den Benutzer aus
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('userID', None)
    
    # Informiere den Benutzer, dass das Profil gelöscht wurde
    flash('Dein Profil wurde erfolgreich gelöscht.', 'success')

    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()

    # Weiterleitung zur Startseite
    return redirect(url_for('home')) # Angenommen, du hast eine 'index'-Route

@app.route('/edit-review/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

    # Wenn das Formular abgesendet wurde
    if request.method == 'POST':
        bewertung = request.form.get('bewertung')
        kommentar = request.form.get('kommentar')

        # Aktualisiere die Bewertungen-Tabelle mit den neuen Werten
        try:
            cursor.execute("""
                UPDATE Bewertungen 
                SET Bewertung = %s, Kommentar = %s 
                WHERE BewertungsID = %s
                """, (bewertung, kommentar, review_id))
            conn.commit()

            flash('Bewertung erfolgreich aktualisiert!', 'success')
            return redirect(url_for('profile'))  # or redirect to any other endpoint
        except Exception as e:
            flash('Ein Fehler ist aufgetreten. Die Bewertung konnte nicht aktualisiert werden.', 'error')
            print(e)  # or log the error
        finally:
            # Schließe die Datenbankverbindung am Ende der Route
            cursor.close()
            conn.close()
            redirect(url_for('profile')) # Assuming you want to redirect to profile after a post request as well.

    # Für GET-Anfragen:
    # Holt die Rezension mithilfe der review_id
    cursor.execute("SELECT * FROM Bewertungen WHERE BewertungsID = %s", (review_id,))
    review = cursor.fetchone()    
    if not review:
        flash("Rezension nicht gefunden!")
        return redirect(url_for('profile'))  # Annahme, dass Sie eine Funktion namens profile_page haben
    
    # Schließe die Datenbankverbindung am Ende der Route
    cursor.close()
    conn.close()
    
    return render_template('edit_review.html', review=review)  # Das sollte 'edit_review.html' und nicht 'profile' sein.

@app.route('/delete-review/<int:review_id>')
def delete_review(review_id):
    # Datenbankverbindung erstellen
    conn, cursor = get_db_connection()

    # Löscht die Rezension mithilfe der review_id
    try:
        cursor.execute("DELETE FROM Bewertungen WHERE BewertungsID = %s", (review_id,))
        conn.commit()
        flash("Rezension erfolgreich gelöscht!")
        return redirect(url_for('profile'))
    except Exception as e:
        conn.rollback()
        print(e)
        flash("Rezension konnte nicht gelöscht werden!")
        return redirect(url_for('profile'))
    finally:
        # Schließe die Datenbankverbindung am Ende der Funktion
        cursor.close()
        conn.close()
        return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)