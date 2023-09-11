from flask_login import UserMixin
from database import (register_user, username_exists, email_exists, 
                      check_user_credentials, get_user_details, get_user_reviews,
                      update_review, get_review_by_id, delete_review_by_id, add_review_for_book, user_has_reviewed_book,
                      delete_user_reviews, delete_user)


class User(UserMixin):

    def __init__(self, user_id=None):
        self.id = user_id
        if user_id:
            self.user_details = self.load_user_details()
        else:
            self.user_details = None

    def register(self, username, email, password, registration_date):
        if username_exists(username):
            return "Benutzername existiert bereits."
        if email_exists(email):
            return "E-Mail existiert bereits."
        
        success = register_user(username, email, password, registration_date)
        if success:
            return "Registrierung erfolgreich!"
        else:
            return "Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut."

    def authenticate(self, username, password):
        user_data = check_user_credentials(username, password)
        if user_data:
            self.id = user_data['UserID']
            self.user_details = self.load_user_details()
            return True
        return False

    def load_user_details(self):
        return get_user_details(self.id)

    def get_reviews(self):
        return get_user_reviews(self.id)

    def add_review(self, buch_id, bewertung, kommentar, date):
        return add_review_for_book(buch_id, self.id, bewertung, kommentar, date)

    def edit_review(self, bewertung, kommentar, review_id):
        return update_review(bewertung, kommentar, review_id)

    def get_review(self, review_id):
        return get_review_by_id(review_id)

    def delete_review(self, review_id):
        return delete_review_by_id(review_id)
    
    def has_reviewed_book(self, book_id):
        return user_has_reviewed_book(self.id, book_id)
    
    def delete(self):
        return delete_user(self.id)
    
    def delete_reviews(self):
        return delete_user_reviews(self.id)
