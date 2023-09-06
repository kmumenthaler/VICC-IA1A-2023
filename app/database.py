
import mysql.connector
from config import DB_CONFIG
from flask import flash

def get_database_config():
    return DB_CONFIG

db_config = get_database_config()

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn, conn.cursor(dictionary=True)

def register_user(username, email, password, registration_date):
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            "INSERT INTO Benutzer (Benutzername, Email, Passwort, Registrierungsdatum) VALUES (%s, %s, %s, %s)",
            (username, email, password, registration_date)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(e)
        return False
    finally:
        cursor.close()
        conn.close()
        
def username_exists(username):
    """Prüft, ob der Benutzername bereits existiert."""
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            "SELECT 1 FROM Benutzer WHERE Benutzername=%s", (username,)
        )
        return bool(cursor.fetchone())
    except Exception as e:
        print(e)
        return False
    finally:
        cursor.close()
        conn.close()

def email_exists(email):
    """Prüft, ob die E-Mail bereits existiert."""
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            "SELECT 1 FROM Benutzer WHERE Email=%s", (email,)
        )
        return bool(cursor.fetchone())
    except Exception as e:
        print(e)
        return False
    finally:
        cursor.close()
        conn.close()

def check_user_credentials(username, password):
    conn, cursor = get_db_connection()
    
    cursor.execute(
        "SELECT Passwort, UserID FROM Benutzer WHERE Benutzername=%s", (username,)
    )
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if result and result['Passwort'] == password:
        return result
    return None

def get_newest_books(limit=5):
    conn, cursor = get_db_connection()
    newest_books_query = "SELECT * FROM Bücher ORDER BY BuchID DESC LIMIT %s"
    cursor.execute(newest_books_query, (limit,))
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return books

def get_popular_books(limit=5):
    conn, cursor = get_db_connection()
    popular_books_query = """
    SELECT Bücher.*, AVG(Bewertungen.Bewertung) as avg_rating
    FROM Bücher
    JOIN Bewertungen ON Bücher.BuchID = Bewertungen.BuchID
    GROUP BY Bücher.BuchID
    ORDER BY avg_rating DESC, Bücher.BuchID DESC 
    LIMIT %s
    """
    cursor.execute(popular_books_query, (limit,))
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return books

def get_latest_reviews(limit=5):
    conn, cursor = get_db_connection()
    
    latest_reviews_query = """
    SELECT Benutzer.Benutzername, Bücher.Titel, Bewertungen.Bewertung, Bewertungen.Kommentar, Bewertungen.Datum 
    FROM Bewertungen
    JOIN Benutzer ON Bewertungen.UserID = Benutzer.UserID
    JOIN Bücher ON Bewertungen.BuchID = Bücher.BuchID
    ORDER BY Bewertungen.Datum DESC
    LIMIT %s
    """
    
    cursor.execute(latest_reviews_query, (limit,))
    reviews = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return reviews

def get_all_books():
    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM Bücher")
    books = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return books

def get_book_details(book_id):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM Bücher WHERE BuchID = %s", (book_id,))
    details = cursor.fetchone()
    cursor.close()
    conn.close()
    return details

def delete_user_reviews(user_id):
    conn, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM Bewertungen WHERE UserID = %s", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        cursor.close()
        conn.close()

def delete_user(user_id):
    conn, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM Benutzer WHERE UserID = %s", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        cursor.close()
        conn.close()

def add_new_book(title, author, description, img_path, publishingyear):
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            "INSERT INTO Bücher (Titel, Autor, Zusammenfassung, Bild, Erscheinungsjahr) VALUES (%s, %s, %s, %s, %s)",
            (title, author, description, img_path, publishingyear)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(e)
        return False
    finally:
        cursor.close()
        conn.close()

def get_book_ratings(book_id):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT Bewertung FROM Bewertungen WHERE BuchID = %s", (book_id,))
    ratings = cursor.fetchall()
    cursor.close()
    conn.close()
    return ratings

def get_book_reviews_and_comments(book_id):
    conn, cursor = get_db_connection()
    cursor.execute(
        """
        SELECT b.Bewertung, b.Kommentar, u.Benutzername 
        FROM Bewertungen b 
        INNER JOIN Benutzer u ON b.UserID = u.UserID 
        WHERE b.BuchID = %s
        """, 
        (book_id,)
    )
    reviews_and_comments = cursor.fetchall()
    cursor.close()
    conn.close()
    return reviews_and_comments

def get_review_count_for_book(book_id):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT COUNT(*) FROM Bewertungen WHERE BuchID = %s", (book_id,))
    count = cursor.fetchone()['COUNT(*)']
    cursor.close()
    conn.close()
    return count

def user_has_reviewed_book(user_id, book_id):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT 1 FROM Bewertungen WHERE UserID = %s AND BuchID = %s", (user_id, book_id))
    result = bool(cursor.fetchone())
    cursor.close()
    conn.close()
    return result

def add_review_for_book(buch_id, user_id, bewertung, kommentar, date):
    conn, cursor = get_db_connection()
    try:
        cursor.execute(
            "INSERT INTO Bewertungen (BuchID, UserID, Bewertung, Kommentar, Datum) VALUES (%s, %s, %s, %s, %s)",
            (buch_id, user_id, bewertung, kommentar, date)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)
    finally:
        cursor.close()
        conn.close()

def get_buch_info(buch_id):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM Bücher WHERE BuchID = %s", (buch_id,))
    buch_info = cursor.fetchone()
    cursor.close()
    conn.close()
    return buch_info

def get_user_details(user_id):
    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM Benutzer WHERE UserID = %s", (user_id,))
    user_details = cursor.fetchone()
    cursor.close()
    conn.close()
    return user_details

def get_user_reviews(user_id):
    conn, cursor = get_db_connection()
    cursor.execute("""
    SELECT b.*, br.BewertungsID, br.Bewertung, br.Kommentar, br.Datum 
    FROM Bewertungen br
    INNER JOIN Bücher b ON b.BuchID = br.BuchID
    WHERE br.UserID = %s
    """, (user_id,))
    user_reviews = cursor.fetchall()
    cursor.close()
    conn.close()
    return user_reviews

def update_review(bewertung, kommentar, review_id):
    # Aktualisiert eine Rezension in der Datenbank basierend auf ihrer ID.
    conn, cursor = get_db_connection()
    try:
        cursor.execute("""
            UPDATE Bewertungen 
            SET Bewertung = %s, Kommentar = %s 
            WHERE BewertungsID = %s
            """, (bewertung, kommentar, review_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)  # or log the error
        return False
    finally:
        cursor.close()
        conn.close()
    return True

def get_review_by_id(review_id):
    # Holt eine Rezension aus der Datenbank basierend auf ihrer ID.
    conn, cursor = get_db_connection()
    cursor.execute("SELECT * FROM Bewertungen WHERE BewertungsID = %s", (review_id,))
    review = cursor.fetchone()
    cursor.close()
    conn.close()
    return review

def delete_review_by_id(review_id):
    # Löscht eine Rezension aus der Datenbank basierend auf ihrer ID.
    conn, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM Bewertungen WHERE BewertungsID = %s", (review_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(e)  # or log the error
        return False
    finally:
        cursor.close()
        conn.close()
    return True