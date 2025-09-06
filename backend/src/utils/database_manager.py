"""
Database Management utilities per eliminare duplicazioni di gestione database.
Fornisce context manager per transazioni automatiche e gestione errori centralizzata.
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple, Generator
import mariadb

from utils.database import get_db_connection, close_db_resources
from fastapi import HTTPException, status


def _raise_http_from_integrity_error(e: mariadb.IntegrityError) -> None:
    error_msg = str(e).lower()
    if "duplicate entry" in error_msg or "unique constraint" in error_msg:
        if "email" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un utente con questa email esiste già."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Errore: dato duplicato rilevato."
            )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Errore di integrità dei dati: {str(e)}"
    )


@contextmanager
def db_transaction(dictionary: bool = True) -> Generator[Tuple[mariadb.Connection, mariadb.Cursor], None, None]:
    """
    Context manager per gestione automatica di connessioni, cursor, commit/rollback.
    
    Args:
        dictionary (bool): Se True, il cursor restituisce risultati come dizionari
        
    Yields:
        Tuple[mariadb.Connection, mariadb.Cursor]: Connessione e cursor del database
        
    Raises:
        HTTPException: Per errori di database con messaggi appropriati
        
    Usage:
        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT * FROM table")
            # Commit automatico se tutto va bene
            # Rollback automatico in caso di eccezioni
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=dictionary)
        
        yield conn, cursor
        
        # Se arriviamo qui senza eccezioni, facciamo commit
        conn.commit()
        
    except mariadb.IntegrityError as e:
        if conn:
            conn.rollback()
        _raise_http_from_integrity_error(e)
            
    except mariadb.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno durante l'operazione database."
        )
    finally:
        close_db_resources(conn, cursor)


@contextmanager
def db_readonly(dictionary: bool = True) -> Generator[mariadb.Cursor, None, None]:
    """
    Context manager per operazioni di sola lettura sul database.

    Crea connessione + cursor e li chiude automaticamente. Non esegue commit.

    Args:
        dictionary (bool): Se True, il cursor restituisce risultati come dizionari.

    Yields:
        mariadb.Cursor: Cursor configurato per la lettura.

    Raises:
        HTTPException: In caso di errori del database.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        # Evita transazioni implicite per SELECT semplici
        try:
            conn.autocommit = True
        except Exception:
            pass
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
    except mariadb.Error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore durante un'operazione di lettura dal database."
        )
    finally:
        close_db_resources(conn, cursor)


def check_record_exists(cursor: mariadb.Cursor, table: str, field: str, value: Any) -> bool:
    """
    Verifica se un record esiste nella tabella specificata.
    
    Args:
        cursor: Cursor del database
        table: Nome della tabella
        field: Nome del campo da verificare
        value: Valore da cercare
        
    Returns:
        bool: True se il record esiste, False altrimenti
    """
    query = f"SELECT 1 FROM {table} WHERE {field} = ? LIMIT 1"
    cursor.execute(query, (value,))
    return cursor.fetchone() is not None


def get_user_profile_data(cursor: mariadb.Cursor, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Recupera i dati del profilo utente (paziente o medico) usando LEFT JOIN.
    
    Args:
        cursor: Cursor del database
        user_id: ID dell'utente
        
    Returns:
        Dict con i dati del profilo o None se non trovato
    """
    query = """
        SELECT
            u.id, u.email, u.tipo_utente,
            COALESCE(p.nome, m.nome) AS nome,
            p.id AS paziente_id,
            m.id AS medico_id
        FROM Utenti u
        LEFT JOIN Pazienti p ON u.id = p.utente_id
        LEFT JOIN Medici m ON u.id = m.utente_id
        WHERE u.id = ?
    """
    cursor.execute(query, (user_id,))
    return cursor.fetchone()


def validate_specialization_exists(cursor: mariadb.Cursor, specialization_id: int) -> bool:
    """
    Verifica se una specializzazione medica esiste.
    
    Args:
        cursor: Cursor del database
        specialization_id: ID della specializzazione
        
    Returns:
        bool: True se esiste, False altrimenti
        
    Raises:
        HTTPException: Se la specializzazione non esiste
    """
    if not check_record_exists(cursor, "Specializzazioni", "id", specialization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La specializzazione con ID {specialization_id} non esiste."
        )
    return True


def get_doctor_profile_id(cursor: mariadb.Cursor, user_id: int) -> int:
    """
    Recupera l'ID del profilo medico dato l'user_id.
    
    Args:
        cursor: Cursor del database
        user_id: ID dell'utente
        
    Returns:
        int: ID del profilo medico
        
    Raises:
        HTTPException: Se il profilo medico non esiste
    """
    cursor.execute("SELECT id FROM Medici WHERE utente_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profilo medico non trovato."
        )
    return result['id'] if isinstance(result, dict) else result[0]


def get_patient_profile_id(cursor: mariadb.Cursor, user_id: int) -> int:
    """
    Recupera l'ID del profilo paziente dato l'user_id.
    
    Args:
        cursor: Cursor del database
        user_id: ID dell'utente
        
    Returns:
        int: ID del profilo paziente
        
    Raises:
        HTTPException: Se il profilo paziente non esiste
    """
    cursor.execute("SELECT id FROM Pazienti WHERE utente_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profilo paziente non trovato."
        )
    return result['id'] if isinstance(result, dict) else result[0]


def execute_insert_get_id(cursor: mariadb.Cursor, query: str, params: Tuple) -> int:
    """
    Esegue una query INSERT e restituisce l'ID dell'ultimo record inserito.
    
    Args:
        cursor: Cursor del database
        query: Query SQL di inserimento
        params: Parametri per la query
        
    Returns:
        int: ID dell'ultimo record inserito
    """
    cursor.execute(query, params)
    return cursor.lastrowid


# (Funzioni helper di SELECT rimosse perché non utilizzate)
