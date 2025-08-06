-- Script di Seeding per il Database HADB
-- Contiene dati di esempio per testare le funzionalità dell'app

USE HADB;

-- Per semplicità, la password per tutti gli utenti è 'password123'
SET @pwd_hash = '$2b$12$isOKlAZsvw8CkSOsugAQ7uvhtoEZVqOCH.T0zPF3PqO0UPE68ngbC';

-- 1. PULIZIA DELLE TABELLE (per riesecuzione sicura dello script)
-- Disabilita i controlli sulle chiavi esterne per permettere un troncamento pulito
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE Valutazioni;
TRUNCATE TABLE Prenotazioni;
TRUNCATE TABLE Disponibilita;
TRUNCATE TABLE Pazienti;
TRUNCATE TABLE Medici;
TRUNCATE TABLE Utenti;
-- Riabilita i controlli
SET FOREIGN_KEY_CHECKS = 1;

-- Creazione Utenti Pazienti
INSERT INTO Utenti (id, email, password_hash, tipo_utente) VALUES
(1, 'paolo.bianchi@email.com', @pwd_hash, 'paziente'),
(2, 'giulia.verdi@email.com', @pwd_hash, 'paziente'),
(3, 'marco.gialli@email.com', @pwd_hash, 'paziente'),
(4, 'sofia.russo@email.com', @pwd_hash, 'paziente'),
(5, 'andrea.ferrari@email.com', @pwd_hash, 'paziente');

INSERT INTO Pazienti (id, utente_id, nome, cognome, telefono) VALUES
(1, 1, 'Paolo', 'Bianchi', '3331112233'),
(2, 2, 'Giulia', 'Verdi', '3334445566'),
(3, 3, 'Marco', 'Gialli', '3345556677'),
(4, 4, 'Sofia', 'Russo', '3356667788'),
(5, 5, 'Andrea', 'Ferrari', '3387778899');

-- Creazione Utenti Medici
INSERT INTO Utenti (id, email, password_hash, tipo_utente) VALUES
(6, 'anna.rossi@email.com', @pwd_hash, 'medico'), -- Cardiologa, Roma
(7, 'luca.neri@email.com', @pwd_hash, 'medico'),    -- Dermatologo, Milano
(8, 'mario.esposito@email.com', @pwd_hash, 'medico'), -- Ortopedico, Napoli
(9, 'elisa.romano@email.com', @pwd_hash, 'medico'), -- Pediatra, Torino
(10, 'fabio.conti@email.com', @pwd_hash, 'medico'); -- Neurologo, Roma

INSERT INTO Medici (id, utente_id, specializzazione_id, nome, cognome, citta, telefono, ordine_iscrizione, numero_iscrizione, provincia_iscrizione, indirizzo_studio, latitudine, longitudine) VALUES
(1, 6, 10, 'Anna', 'Rossi', 'Roma', '3389998877', 'Ordine dei Medici di Roma', 'RM12345', 'RM', 'Via del Corso 1, 00186, Roma', 41.905433, 12.482266),          -- Spec: Cardiologia
(2, 7, 18, 'Luca', 'Neri', 'Milano', '3396665544', 'Ordine dei Medici di Milano', 'MI67890', 'MI', 'Piazza del Duomo 12, 20122, Milano', 45.464211, 9.191383),    -- Spec: Dermatologia
(3, 8, 45, 'Mario', 'Esposito', 'Napoli', '3471122334', 'Ordine dei Medici di Napoli', 'NA54321', 'NA', 'Via Toledo 100, 80134, Napoli', 40.842186, 14.248694),     -- Spec: Ortopedia
(4, 9, 47, 'Elisa', 'Romano', 'Torino', '3482233445', 'Ordine dei Medici di Torino', 'TO98765', 'TO', 'Via Roma 50, 10121, Torino', 45.067755, 7.682489),       -- Spec: Pediatria
(5, 10, 40, 'Fabio', 'Conti', 'Roma', '3493344556', 'Ordine dei Medici di Roma', 'RM24680', 'RM', 'Viale Trastevere 20, 00153 Roma', 41.883980, 12.472900); -- Spec: Neurologia

-- Creazione Disponibilità per Medici
-- Medico 1: Anna Rossi
INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine) VALUES 
(1, '2025-08-11 09:00:00', '2025-08-11 09:30:00'), (1, '2025-08-11 09:30:00', '2025-08-11 10:00:00'),
(1, '2025-08-12 15:00:00', '2025-08-12 15:30:00'), (1, '2025-08-12 15:30:00', '2025-08-12 16:00:00'),
(1, '2025-08-13 10:00:00', '2025-08-13 10:30:00');

-- Medico 2: Luca Neri
INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine) VALUES
(2, '2025-08-13 11:00:00', '2025-08-13 11:30:00'), (2, '2025-08-13 11:30:00', '2025-08-13 12:00:00'),
(2, '2025-08-14 16:00:00', '2025-08-14 16:30:00'), (2, '2025-08-14 16:30:00', '2025-08-14 17:00:00');

-- Medico 3: Mario Esposito
INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine) VALUES
(3, '2025-08-11 14:00:00', '2025-08-11 14:30:00'), (3, '2025-08-11 14:30:00', '2025-08-11 15:00:00'),
(3, '2025-08-15 09:00:00', '2025-08-15 09:30:00');

-- Medico 4: Elisa Romano
INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine) VALUES
(4, '2025-08-12 09:00:00', '2025-08-12 09:30:00'), (4, '2025-08-12 09:30:00', '2025-08-12 10:00:00'),
(4, '2025-08-18 17:00:00', '2025-08-18 17:30:00');

-- Medico 5: Fabio Conti
INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine) VALUES
(5, '2025-08-13 16:00:00', '2025-08-13 16:30:00'), (5, '2025-08-13 16:30:00', '2025-08-13 17:00:00'),
(5, '2025-08-19 11:00:00', '2025-08-19 11:30:00');

-- Creazione Prenotazioni
-- Prenotazione #1 (Completata)
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato, note_paziente) VALUES (2, 1, 'Completata', 'Controllo generale annuale.');
UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = 2;

-- Prenotazione #2 (Confermata)
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato, note_paziente) VALUES (3, 2, 'Confermata', 'Vorrei un consulto per dolore al petto.');
UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = 3;

-- Prenotazione #3 (Completata)
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato, note_paziente) VALUES (6, 3, 'Completata', 'Visita per sfogo cutaneo.');
UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = 6;

-- Prenotazione #4 (Completata)
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato) VALUES (7, 4, 'Completata');
UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = 7;

-- Prenotazione #5 (Completata)
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato) VALUES (10, 5, 'Completata');
UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = 10;

-- Prenotazione #6 (Cancellata)
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato) VALUES (11, 1, 'Cancellata');
UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = 11;

-- Prenotazione #7 (Completata)
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato) VALUES (13, 2, 'Completata');
UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = 13;

-- Creazione Valutazioni
-- Valutazione per Prenotazione #1 (Dott.ssa Rossi)
INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento) VALUES (1, 1, 1, 5, 'Dottoressa molto competente e gentile. Mi sono trovato benissimo.');

-- Valutazione per Prenotazione #3 (Dott. Neri)
INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento) VALUES (3, 3, 2, 4, 'Visita accurata, medico professionale ma un po frettoloso.');

-- Valutazione per Prenotazione #4 (Dott. Neri)
INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento) VALUES (4, 4, 2, 5, 'Perfetto! Ha risolto il mio problema in pochi minuti.');

-- Valutazione per Prenotazione #5 (Dott. Esposito)
INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento) VALUES (5, 5, 3, 5, 'Un vero professionista, mi ha spiegato tutto con grande pazienza.');

-- Valutazione per Prenotazione #7 (Dott.ssa Romano)
INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento) VALUES (7, 2, 4, 4, 'Molto brava con i bambini, mia figlia non ha avuto paura.');

-- Aggiungo una seconda valutazione per la Dott.ssa Rossi per testare meglio la media
INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine, is_prenotato) VALUES (1, '2025-08-01 10:00:00', '2025-08-01 10:30:00', TRUE);
SET @last_disp_id_val = LAST_INSERT_ID();
INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato) VALUES (@last_disp_id_val, 3, 'Completata');
SET @last_pren_id_val = LAST_INSERT_ID();
INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento) VALUES (@last_pren_id_val, 3, 1, 4, 'Tutto ok, visita di controllo senza problemi.');
