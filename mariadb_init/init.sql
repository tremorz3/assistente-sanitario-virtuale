CREATE DATABASE IF NOT EXISTS HADB;

USE HADB;

CREATE USER IF NOT EXISTS 'user'@'%' IDENTIFIED BY 'pwd';
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE ON HADB.* TO 'user'@'%';
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
    specializzazione_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    citta VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    ordine_iscrizione VARCHAR(255) NOT NULL,
    numero_iscrizione VARCHAR(50) NOT NULL,
    provincia_iscrizione VARCHAR(50) NOT NULL,
    -- Campi impostati inizialente a NULL per la fase di sviluppo
    indirizzo_studio VARCHAR(255) NOT NULL,
    latitudine DECIMAL(10, 8) NOT NULL,
    longitudine DECIMAL(11, 8) NOT NULL,
    punteggio_medio DECIMAL(3, 2) NOT NULL DEFAULT 0.00, -- Aggiornato automaticamente con un trigger
    FOREIGN KEY (utente_id) REFERENCES Utenti(id) ON DELETE CASCADE,
    FOREIGN KEY (specializzazione_id) REFERENCES Specializzazioni(id)
);

CREATE TABLE IF NOT EXISTS Pazienti (
    id INT PRIMARY KEY AUTO_INCREMENT,
    utente_id INT NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    FOREIGN KEY (utente_id) REFERENCES Utenti(id) ON DELETE CASCADE
);

-- Tabella per le fasce orarie rese disponibili di un medico
CREATE TABLE IF NOT EXISTS Disponibilita (
    id INT PRIMARY KEY AUTO_INCREMENT,
    medico_id INT NOT NULL,
    data_ora_inizio DATETIME NOT NULL,
    data_ora_fine DATETIME NOT NULL,
    is_prenotato BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (medico_id) REFERENCES Medici(id) ON DELETE CASCADE,
    INDEX idx_medico_data (medico_id, data_ora_inizio) -- Indice per velocizzare la ricerca di disponibilità per il medico X a partire da oggi
);

-- Tabella per le prenotazioni effettuate da un paziente
CREATE TABLE IF NOT EXISTS Prenotazioni (
    id INT PRIMARY KEY AUTO_INCREMENT,
    disponibilita_id INT NOT NULL UNIQUE, -- Una disponibilità può essere prenotata solo una volta
    paziente_id INT NOT NULL,
    data_prenotazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stato ENUM('Confermata', 'Completata', 'Cancellata') NOT NULL DEFAULT 'Confermata',
    note_paziente TEXT,
    FOREIGN KEY (disponibilita_id) REFERENCES Disponibilita(id) ON DELETE CASCADE,
    FOREIGN KEY (paziente_id) REFERENCES Pazienti(id) ON DELETE CASCADE
);

-- Tabella per le valutazioni lasciate da un paziente dopo una visita
CREATE TABLE IF NOT EXISTS Valutazioni (
    id INT PRIMARY KEY AUTO_INCREMENT,
    prenotazione_id INT NOT NULL UNIQUE, -- Ogni prenotazione può avere al massimo una valutazione
    paziente_id INT NOT NULL,
    medico_id INT NOT NULL,
    punteggio INT NOT NULL CHECK (punteggio >= 1 AND punteggio <= 5), -- Punteggio da 1 a 5
    commento TEXT,
    data_valutazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prenotazione_id) REFERENCES Prenotazioni(id) ON DELETE CASCADE,
    FOREIGN KEY (paziente_id) REFERENCES Pazienti(id) ON DELETE CASCADE,
    FOREIGN KEY (medico_id) REFERENCES Medici(id) ON DELETE CASCADE
);

INSERT INTO Specializzazioni (nome) VALUES
('Allergologia'),
('Andrologia'),
('Angiologia'),
('Audioprotesista'),
('Cardiochirurgia'),
('Cardiologia'),
('Chirurgia Generale'),
('Chirurgia Maxillo-Facciale'),
('Chirurgia Plastica ed Estetica'),
('Chirurgia Toracica'),
('Chirurgia Vascolare'),
('Dermatologia e Venerologia'),
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
('Logopedia'),
('Medicina dello Sport'),
('Medicina Legale'),
('Medico di Medicina Generale'),
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
('Psichiatria'),
('Radiologia e Radiologia Diagnostica'),
('Reumatologia'),
('Urologia')
ON DUPLICATE KEY UPDATE nome=nome; -- Evita errori se si esegue lo script più volte

-- RIGGER PER AGGIORNARE IL PUNTEGGIO MEDIO DEL MEDICO
DELIMITER $$

CREATE TRIGGER after_valutazione_insert
AFTER INSERT ON Valutazioni
FOR EACH ROW
BEGIN
    -- Calcola la nuova media dei punteggi per il medico specifico
    DECLARE nuova_media DECIMAL(3, 2);
    
    SELECT AVG(punteggio) INTO nuova_media
    FROM Valutazioni
    WHERE medico_id = NEW.medico_id;
    
    -- Aggiorna la tabella Medici con la nuova media
    UPDATE Medici
    SET punteggio_medio = nuova_media
    WHERE id = NEW.medico_id;
END$$

DELIMITER ;