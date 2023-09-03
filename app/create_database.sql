-- Erstellung der Datenbank
CREATE DATABASE BuchrezensionsPlattform;
USE BuchrezensionsPlattform;

-- Erstellung der Benutzer-Tabelle
CREATE TABLE Benutzer (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Benutzername VARCHAR(255) NOT NULL UNIQUE,
    Email VARCHAR(255) NOT NULL UNIQUE,
    Passwort VARCHAR(255) NOT NULL,
    Registrierungsdatum DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Erstellung der Bücher-Tabelle
CREATE TABLE Bücher (
    BuchID INT PRIMARY KEY AUTO_INCREMENT,
    Titel VARCHAR(255) NOT NULL,
    Autor VARCHAR(255) NOT NULL,
    Erscheinungsjahr INT,
    Zusammenfassung TEXT,
    Bild VARCHAR(255) -- Dies kann ein Link oder ein Pfad zu einem Bild sein
);

-- Erstellung der Bewertungen-Tabelle
CREATE TABLE Bewertungen (
    BewertungsID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    BuchID INT,
    Bewertung INT CHECK (Bewertung >= 1 AND Bewertung <= 5),
    Kommentar TEXT,
    Datum DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Benutzer(UserID),
    FOREIGN KEY (BuchID) REFERENCES Bücher(BuchID)
);

