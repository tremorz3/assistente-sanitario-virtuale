'''
Lo scopo di questo file è centralizzare tutta la logica per la connessione al database e le operazioni di base sui dati.
'''
import mariadb
import os                
from dotenv import load_dotenv # Funzione specifica per caricare il file .env

load_dotenv()  # Carica le variabili d'ambiente dal file .env

DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
DB_NAME: str = os.getenv("DB_NAME", "HADB")
DB_USER: str = os.getenv("DB_USER", "user")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "pwd")

def get_db_connection() -> mariadb.Connection:
    """
    Crea e restituisce una connessione al database MariaDB.

    Returns:
        mariadb.Connection: Oggetto di connessione al database.
    Raises:
        mariadb.Error: Se si verifica un errore durante la connessione al database.
    """
    try:
        conn = mariadb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        return conn
    except mariadb.Error as e:
        print(f"Errore di connessione al database HADB: {e}")
        raise e  # lancia l'errore per gestirlo a livello superiore

def close_db_resources(conn: mariadb.Connection, cursor: mariadb.Cursor) -> None:
    """
    Chiude in modo sicuro il cursore e la connessione al database.
    """
    if cursor:
        cursor.close()
    if conn:
        conn.close()
