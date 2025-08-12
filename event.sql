-- events.sql

USE HADB;

-- Impostiamo il delimitatore per poter scrivere il corpo dell'evento
DELIMITER $$

-- Creiamo l'evento schedulato per la pulizia delle disponibilità
CREATE EVENT IF NOT EXISTS `cleanup_vecchie_disponibilita`
ON SCHEDULE
    -- Esegui questo evento ogni giorno, partendo da adesso
    EVERY 1 DAY
    STARTS CURRENT_TIMESTAMP
COMMENT 'Pulisce le fasce orarie di disponibilità vecchie e non prenotate.'
DO
BEGIN
    -- L'operazione di cancellazione vera e propria:
    -- Cancella tutte le righe dalla tabella Disponibilita
    -- la cui data di fine è passata E che non sono state prenotate.
    -- La condizione "is_prenotato = FALSE" è FONDAMENTALE per non cancellare
    -- lo storico degli appuntamenti che sono stati effettivamente prenotati.
    DELETE FROM Disponibilita
    WHERE
        data_ora_fine < NOW() AND is_prenotato = FALSE;
END$$

-- Reimpostiamo il delimitatore standard
DELIMITER ;

-- Nota: Il Docker container ufficiale di MariaDB ha l'event scheduler
-- abilitato di default (event_scheduler=ON), quindi questo dovrebbe
-- funzionare senza ulteriori configurazioni.

-- Per il momento il file si trova fuori mariadb_init perchè siamo in fase di testing