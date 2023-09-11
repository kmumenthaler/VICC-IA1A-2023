from database import *
import config
from flask import render_template, redirect, url_for, flash, session, request
from datetime import datetime

def compute_average_rating(ratings):
    """Berechnet den durchschnittlichen Wert einer Liste von Bewertungen"""
    if ratings:
        return round(sum(ratings) / len(ratings))
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def check_user_credentials(username, password):
    """Überprüfen der Benutzeranmeldedaten."""
    return get_user_by_credentials(username, password)

def get_user_by_credentials(username, password):
    """Abfrage des Benutzers anhand von Benutzername und Passwort."""
    # Diese Funktion kann nach Bedarf erweitert werden, um z.B. das Passwort zu verschlüsseln.
    return check_user_credentials(username, password)

def set_user_session(user, username):
    """Setzen der Sitzungsvariablen nach erfolgreicher Anmeldung."""
    session['logged_in'] = True
    session['username'] = username
    session['userID'] = user['UserID']

def redirect_to_home():
    """Weiterleiten des Benutzers zur Startseite."""
    return redirect(url_for('home'))

def flash_login_error():
    """Anzeigen einer Fehlermeldung bei falschen Anmeldedaten."""
    flash('Falscher Benutzername oder Passwort!')

def render_login_page():
    """Rendern der Login-Seite."""
    return render_template('login.html')

def is_strong_password(password):
    """Prüft, ob das Passwort stark genug ist."""
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isalpha() for char in password):
        return False
    return True

def is_valid_email(email):
    """Überprüft die Gültigkeit der E-Mail."""
    if '@' not in email or '.' not in email:
        return False
    return True

def get_user_input():
    """Ruft die Benutzereingabe vom Formular ab."""
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    return username, email, password, confirm_password

def passwords_match(password, confirm_password):
    """Überprüft, ob die beiden Passwörter übereinstimmen."""
    return password == confirm_password

def register_new_user(username, email, password):
    """Registriert einen neuen Benutzer und gibt True zurück, wenn erfolgreich, sonst False."""
    current_date = datetime.now().date()
    return register_user(username, email, password, current_date)

def flash_registration_error():
    """Zeigt eine Fehlermeldung an, wenn die Registrierung fehlschlägt."""
    flash('Ein Fehler ist aufgetreten. Versuchen Sie es später erneut.')

def render_registration_page():
    """Rendert die Registrierungsseite."""
    return render_template('register.html')