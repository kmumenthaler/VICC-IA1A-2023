from utils import *
import config
from database import *
from utils import compute_average_rating
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, current_user
import mysql.connector
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

@app.route('/')
def home():
    # 5 neueste Bücher
    newest_books = get_newest_books()

    # Beliebteste Bücher (wir nehmen hier auch 5)
    popular_books = get_popular_books()

    # Benutzeraktivität: 5 neueste Bewertungen
    latest_reviews = get_latest_reviews()

    return render_template('home.html', newest_books=newest_books, popular_books=popular_books, latest_reviews=latest_reviews)

@app.route('/books')
def books():
    buecher = get_all_books()

    # Füge die durchschnittliche Bewertung zu jedem Buch hinzu
    for buch in buecher:
        bewertungen = get_book_ratings(buch['BuchID'])
        ratings = [bewertung['Bewertung'] for bewertung in bewertungen]
        buch['DurchschnittlicheBewertung'] = compute_average_rating(ratings)

    return render_template('books.html', buecher=buecher)

@app.route('/book/<int:book_id>', methods=['GET'])
def book_detail(book_id):
    buch = get_book_details(book_id)
    bewertungen = get_book_reviews_and_comments(book_id)
    kommentare = bewertungen
    ratings = [bewertung['Bewertung'] for bewertung in bewertungen]
    durchschnittliche_bewertung = compute_average_rating(ratings)
    bewertungs_anzahl = get_review_count_for_book(book_id)
    
    user_id = session.get('userID')
    hat_bewertet = False
    if user_id:
        hat_bewertet = user_has_reviewed_book(user_id, book_id)

    return render_template('book_detail.html', buch=buch, durchschnittliche_bewertung=durchschnittliche_bewertung, kommentare=kommentare, hat_bewertung_abgegeben=hat_bewertet, bewertungen=bewertungen, bewertungs_anzahl=bewertungs_anzahl)

@app.route('/buch/<int:buch_id>/bewertung_abgeben', methods=['GET', 'POST'])
def bewertung_abgeben(buch_id):
    if not session.get('logged_in', False):
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))
    
    user_id = session.get('userID')
    if user_has_reviewed_book(user_id, buch_id):  # Die Überprüfung wurde nach dem Login-Check verschoben
        flash('Sie haben bereits eine Bewertung für dieses Buch abgegeben.')
        return redirect(url_for('book_detail', book_id=buch_id))

    if request.method == 'POST':        
        bewertung = request.form.get('bewertung')
        kommentar = request.form.get('kommentar')
        current_date = datetime.now().date()
        try:
            add_review_for_book(buch_id, user_id, bewertung, kommentar, current_date)
            
            flash('Ihre Bewertung wurde erfolgreich abgegeben!')
        except Exception as e:
            
            flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')
            print(e)

        return redirect(url_for('book_detail', book_id=buch_id))

    buch = get_buch_info(buch_id)
    return render_template('bewertung_abgeben.html', buch=buch)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, email, password, confirm_password = get_user_input()

        # Überprüfen, ob alle Felder ausgefüllt sind
        if not all([username, email, password, confirm_password]):
            flash('Alle Felder müssen ausgefüllt sein.')
            return render_registration_page()

        # Überprüfen, ob die Passwörter übereinstimmen
        if not passwords_match(password, confirm_password):
            flash('Die Passwörter stimmen nicht überein.')
            return render_registration_page()

        # Überprüfen der Passwortstärke
        if not is_strong_password(password):
            flash('Das Passwort muss mindestens 8 Zeichen lang sein und eine Kombination aus Buchstaben und Zahlen enthalten.')
            return render_registration_page()

        # Überprüfen, ob der Benutzername bereits existiert
        if username_exists(username):
            flash('Benutzername bereits vergeben.')
            return render_registration_page()

        # Überprüfen, ob die E-Mail bereits existiert und gültig ist
        if not is_valid_email(email) or email_exists(email):
            flash('Ungültige oder bereits verwendete E-Mail-Adresse.')
            return render_registration_page()

        # Benutzer registrieren
        if register_new_user(username, email, password):
            flash('Erfolgreich registriert!')
            return redirect(url_for('home'))
        else:
            flash_registration_error()

    return render_registration_page()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = check_user_credentials(username, password)

        if user:
            set_user_session(user, username)
            flash('Erfolgreich angemeldet!')
            return redirect_to_home()
        else:
            flash_login_error()
    return render_login_page()

@app.route('/logout')
def logout():
    session.clear()
    flash('Erfolgreich abgemeldet!')
    return redirect(url_for('home'))

@app.route('/add-book', methods=['GET', 'POST'])
def add_book():
    if 'logged_in' not in session:
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('titel')
        author = request.form.get('autor')
        description = request.form.get('zusammenfassung')
        file = request.files.get('bookImage')
        publishingyear = request.form.get('erscheinungsjahr')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(config.UPLOAD_FOLDER, filename))
            img_path = os.path.join(config.UPLOAD_FOLDER, filename)
            success = add_new_book(title, author, description, img_path, publishingyear)
            if success:
                flash('Buch erfolgreich hinzugefügt!')
                return redirect(url_for('profile'))
            else:
                flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')
                return redirect(url_for('add_book'))
    
    return render_template('add_book.html')

@app.route('/profile', methods=['GET'])
def profile():
    if 'logged_in' not in session:
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))

    user_id = session.get('userID')
    user = get_user_details(user_id)
    user_reviews = get_user_reviews(user_id)

    total_reviews = len(user_reviews)
    avg_rating = round(sum([r['Bewertung'] for r in user_reviews]) / total_reviews, 2) if user_reviews else None

    return render_template('profile.html', user=user, user_reviews=user_reviews, total_reviews=total_reviews, avg_rating=avg_rating)

@app.route('/delete-profile')
def delete_profile():
    # Überprüfe, ob der Benutzer angemeldet ist
    user_id = session.get('userID')
    if not user_id:
        flash('Du musst angemeldet sein, um dein Profil zu löschen.', 'danger')
        return redirect(url_for('login')) # Angenommen, du hast eine 'login'-Route

    # Lösche alle zugehörigen Daten (z.B. Bewertungen) 
    delete_user_reviews(user_id)

    # Lösche den Benutzer
    delete_user(user_id)

    # Logge den Benutzer aus
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('userID', None)
    
    # Informiere den Benutzer, dass das Profil gelöscht wurde
    flash('Dein Profil wurde erfolgreich gelöscht.', 'success')    

    # Weiterleitung zur Startseite
    return redirect(url_for('home')) # Angenommen, du hast eine 'index'-Route

@app.route('/edit-review/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    # Wenn das Formular abgesendet wurde
    if request.method == 'POST':
        bewertung = request.form.get('bewertung')
        kommentar = request.form.get('kommentar')

        # Aktualisiere die Bewertungen-Tabelle mit den neuen Werten
        if update_review(bewertung, kommentar, review_id):
            flash('Bewertung erfolgreich aktualisiert!', 'success')
            return redirect(url_for('profile'))  # or redirect to any other endpoint
        else:
            flash('Ein Fehler ist aufgetreten. Die Bewertung konnte nicht aktualisiert werden.', 'error')
            return redirect(url_for('profile')) # Assuming you want to redirect to profile after a post request as well.

    # Für GET-Anfragen:
    # Holt die Rezension mithilfe der review_id
    review = get_review_by_id(review_id)
    if not review:
        flash("Rezension nicht gefunden!")
        return redirect(url_for('profile'))  # Annahme, dass Sie eine Funktion namens profile_page haben
    
    return render_template('edit_review.html', review=review)

@app.route('/delete-review/<int:review_id>')
def delete_review(review_id):

    # Löscht die Rezension mithilfe der review_id
    if delete_review_by_id(review_id):
        flash("Rezension erfolgreich gelöscht!")
    else:
        flash("Rezension konnte nicht gelöscht werden!")
    
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)