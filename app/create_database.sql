-- Erstellung der Datenbank
CREATE DATABASE BuchrezensionsPlattform;
USE BuchrezensionsPlattform;

-- Erstellung der Benutzer-Tabelle
CREATE TABLE Benutzer (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Benutzername VARCHAR(255) NOT NULL UNIQUE,
    Email VARCHAR(255) NOT NULL UNIQUE,
    Passwort VARCHAR(255) NOT NULL,
    Registrierungsdatum DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Erstellung der Bücher-Tabelle
CREATE TABLE Bücher (
    BuchID INT AUTO_INCREMENT PRIMARY KEY,
    Titel VARCHAR(255) NOT NULL,
    Autor VARCHAR(255),
    Erscheinungsjahr YEAR,
    Zusammenfassung TEXT
);

-- Erstellung der Bewertungen-Tabelle
CREATE TABLE Bewertungen (
    BewertungsID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT,
    BuchID INT,
    Bewertung INT NOT NULL CHECK (Bewertung BETWEEN 1 AND 5), -- Annahme, dass Bewertungen von 1 bis 5 gehen
    Kommentar TEXT,
    Datum DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Benutzer(UserID),
    FOREIGN KEY (BuchID) REFERENCES Bücher(BuchID)
);

