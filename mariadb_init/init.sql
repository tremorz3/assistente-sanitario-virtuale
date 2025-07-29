CREATE DATABASE IF NOT EXISTS HADB;

USE HADB;

CREATE USER IF NOT EXISTS 'user'@'%' IDENTIFIED BY 'pwd';
GRANT SELECT, INSERT, UPDATE, DELETE ON HADB.* TO 'user'@'%';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS Specializzazioni (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Utenti (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(300) NOT NULL,
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

INSERT INTO Specializzazioni (nome) VALUES
('Agopuntura'),
('Allergologia'),
('Andrologia'),
('Anatomia Patologica'),
('Anestesia'),
('Angiologia'),
('Audioprotesista'),
('Biologia della Riproduzione'),
('Cardiochirurgia'),
('Cardiologia'),
('Certificazione Medica'),
('Chinesiologia'),
('Chiropratica'),
('Chirurgia Generale'),
('Chirurgia Plastica ed Estetica'),
('Chirurgia Specialistica'),
('Chirurgia Toracica'),
('Dermatologia'),
('Diabetologia'),
('Dietologia e Nutrizione'),
('Ematologia'),
('Endocrinologia'),
('Epatologia'),
('Fisiatria'),
('Fisioterapia e Massofisioterapia'),
('Gastroenterologia'),
('Geriatria'),
('Ginecologia'),
('Immunologia'),
('Infettivologia'),
('Internista'),
('Logopedia'),
('Medico di Medicina Generale'),
('Medicina dello Sport'),
('Medicina Estetica'),
('Medicina Legale'),
('Medicina Naturale'),
('Nefrologia'),
('Neurochirurgia'),
('Neurologia'),
('Odontoiatria e Ortodonzia'),
('Oftalmologia (Oculistica)'),
('Oncologia'),
('Ortopedia'),
('Osteopatia'),
('Otorinolaringoiatria'),
('Pediatria'),
('Pneumologia'),
('Podologia'),
('Posturologia'),
('Proctologia'),
('Psichiatria'),
('Psicologia'),
('Psicoterapia'),
('Radiologia e Radiologia Diagnostica'),
('Reumatologia'),
('Senologia'),
('Sessuologia'),
('Terapia del Dolore'),
('Urologia');