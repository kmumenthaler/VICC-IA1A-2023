import os
from utils import *
import config
from database import *
from utils import compute_average_rating
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
from User import User

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Die Route, zu der die Benutzer weitergeleitet werden, wenn sie nicht eingeloggt sind.
login_manager.login_message = 'Bitte melde dich an!'


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def home():
    # 5 neueste Bücher
    newest_books = get_newest_books()

    # Beliebteste Bücher (5 beliebte Bücher)
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
    
    user = current_user
    hat_bewertet = False
    if user.is_authenticated:
        hat_bewertet = user.has_reviewed_book(book_id)

    return render_template('book_detail.html', buch=buch, durchschnittliche_bewertung=durchschnittliche_bewertung, kommentare=kommentare, hat_bewertung_abgegeben=hat_bewertet, bewertungen=bewertungen, bewertungs_anzahl=bewertungs_anzahl)

@app.route('/book/<int:buch_id>/bewertung_abgeben', methods=['GET', 'POST'])
@login_required
def bewertung_abgeben(buch_id):
    # Angemeldeter Benutzer
    user = current_user
    
    if user.has_reviewed_book(buch_id):
        flash('Sie haben bereits eine Bewertung für dieses Buch abgegeben.')
        return redirect(url_for('book_detail', book_id=buch_id))

    if request.method == 'POST':
        bewertung = request.form.get('bewertung')
        kommentar = request.form.get('kommentar')
        date = datetime.now().date()

        user.add_review(buch_id, bewertung, kommentar, date)
        flash('Ihre Bewertung wurde erfolgreich abgegeben!')

        return redirect(url_for('book_detail', book_id=buch_id))

    buch = get_buch_info(buch_id)
    return render_template('bewertung_abgeben.html', buch=buch)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, email, password, confirm_password = get_user_input()
        registration_date = datetime.now().date()

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
        user = User()
        registration_response = user.register(username, email, password, registration_date)

        flash(registration_response)
        if registration_response == "Registrierung erfolgreich!":
            return redirect(url_for('home'))
        else:
            return render_registration_page()

    return render_registration_page()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User()
        if User.authenticate(user, username, password):
            login_user(user)
            flash('Erfolgreich angemeldet!')            
            return redirect_to_home()
        else:
            flash_login_error()
    return render_login_page()

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Erfolgreich abgemeldet!')
    return redirect(url_for('home'))

@app.route('/add-book', methods=['GET', 'POST'])
@login_required
def add_book():
    if not current_user.is_authenticated:
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
@login_required
def profile():
    if not current_user.is_authenticated:
        flash('Bitte melden Sie sich zuerst an!')
        return redirect(url_for('login'))

    user = current_user
    user_details = user.load_user_details()
    user_reviews = user.get_reviews()

    total_reviews = len(user_reviews)
    avg_rating = round(sum([r['Bewertung'] for r in user_reviews]) / total_reviews, 2) if user_reviews else None

    return render_template('profile.html', user=user_details, user_reviews=user_reviews, total_reviews=total_reviews, avg_rating=avg_rating)

@app.route('/delete-profile')
@login_required
def delete_profile():
    user = current_user
    
    # Lösche alle zugehörigen Daten (z.B. Bewertungen) 
    user.delete_reviews()

    # Lösche den Benutzer
    user.delete()

    # Logge den Benutzer aus
    logout_user()
    
    # Informiere den Benutzer, dass das Profil gelöscht wurde
    flash('Dein Profil wurde erfolgreich gelöscht.', 'success')    

    # Weiterleitung zur Startseite
    return redirect(url_for('home'))

@app.route('/edit-review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    user = current_user
    review = user.get_review(review_id)
    if not review:
        flash("Rezension nicht gefunden!")
        return redirect(url_for('profile'))

    if request.method == 'POST':
        bewertung = request.form.get('bewertung')
        kommentar = request.form.get('kommentar')

        user.edit_review(bewertung, kommentar, review_id)
        flash('Bewertung erfolgreich aktualisiert!')

        return redirect(url_for('profile'))

    return render_template('edit_review.html', review=review)

@app.route('/delete-review/<int:review_id>')
@login_required
def delete_review(review_id):
    user = current_user
    if user.delete_review(review_id):
        flash("Rezension erfolgreich gelöscht!")
    else:
        flash("Rezension konnte nicht gelöscht werden!")

    return redirect(url_for('profile'))

@app.route('/exec/hash_pws', methods=['GET'])
def hash_pws():
    hash_existing_passwords()
    return True


######## API ROUTEN ########
# API-Route, um alle Bücher abzurufen
@app.route('/api/books', methods=['GET'])
@login_required
def api_get_books():
    books = get_all_books()
    return jsonify(books)

# API-Route, um ein bestimmtes Buch abzurufen
@app.route('/api/books/<int:book_id>', methods=['GET'])
@login_required
def api_get_book(book_id):
    books = get_buch_info(book_id)  
    return jsonify(books)

# API-Route, um alle Bewertungen für ein bestimmtes Buch abzurufen
@app.route('/api/reviews/<int:book_id>', methods=['GET'])
@login_required
def api_get_reviews_for_book(book_id):
    reviews = get_book_reviews_and_comments(book_id)
    return jsonify(reviews)


    
if __name__ == '__main__':
    app.run(debug=True)