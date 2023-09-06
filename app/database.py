
import mysql.connector

db_config = {
    'host': 'db',
    'user': 'root',
    'password': 'Start123.',
    'database': 'BuchrezensionsPlattform'
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn, conn.cursor(dictionary=True)

def get_newest_books(cursor, limit=5):
    newest_books_query = "SELECT * FROM Bücher ORDER BY BuchID DESC LIMIT %s"
    cursor.execute(newest_books_query, (limit,))
    return cursor.fetchall()

def get_popular_books(cursor, limit=5):
    popular_books_query = """
    SELECT Bücher.*, AVG(Bewertungen.Bewertung) as avg_rating
    FROM Bücher
    JOIN Bewertungen ON Bücher.BuchID = Bewertungen.BuchID
    GROUP BY Bücher.BuchID
    ORDER BY avg_rating DESC, Bücher.BuchID DESC 
    LIMIT %s
    """
    cursor.execute(popular_books_query, (limit,))
    return cursor.fetchall()

def get_latest_reviews(cursor, limit=5):
    latest_reviews_query = """
    SELECT Benutzer.Benutzername, Bücher.Titel, Bewertungen.Bewertung, Bewertungen.Kommentar, Bewertungen.Datum 
    FROM Bewertungen
    JOIN Benutzer ON Bewertungen.UserID = Benutzer.UserID
    JOIN Bücher ON Bewertungen.BuchID = Bücher.BuchID
    ORDER BY Bewertungen.Datum DESC
    LIMIT %s
    """
    cursor.execute(latest_reviews_query, (limit,))
    return cursor.fetchall()

def get_all_books(cursor):
    cursor.execute("SELECT * FROM Bücher")
    return cursor.fetchall()

def get_book_details(cursor, book_id):
    cursor.execute("SELECT * FROM Bücher WHERE BuchID = %s", (book_id,))
    return cursor.fetchone()
