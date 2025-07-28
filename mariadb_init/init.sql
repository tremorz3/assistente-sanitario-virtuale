CREATE DATABASE IF NOT EXISTS HADB;

USE HADB;

CREATE USER IF NOT EXISTS 'user'@'%' IDENTIFIED BY 'pwd';
GRANT ALL PRIVILEGES ON HADB.* TO 'user'@'%';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS Specializzazioni (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Utenti (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(300) NOT NULL,
    password_salt VARCHAR(300) NOT NULL,
    tipo_utente ENUM('medico', 'paziente') NOT NULL,
    data_registrazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Medici (
    id INT PRIMARY KEY AUTO_INCREMENT,
    utente_id INT NOT NULL UNIQUE,
    specializzazione_id INT,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    citta VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    ordine_iscrizione VARCHAR(255) NOT NULL,
    numero_iscrizione VARCHAR(50) NOT NULL,
    provincia_iscrizione VARCHAR(50) NOT NULL,
    FOREIGN KEY (utente_id) REFERENCES Utenti(id) ON DELETE CASCADE,
    FOREIGN KEY (specializzazione_id) REFERENCES Specializzazioni(id)
);

CREATE TABLE IF NOT EXISTS Pazienti (
    id INT PRIMARY KEY AUTO_INCREMENT,
    utente_id INT NOT NULL UNIQUE,
    nome VARCHAR(100),
    cognome VARCHAR(100),
    telefono VARCHAR(20),
    FOREIGN KEY (utente_id) REFERENCES Utenti(id) ON DELETE CASCADE
);