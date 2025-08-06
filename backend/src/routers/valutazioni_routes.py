from fastapi import APIRouter, HTTPException, status
from typing import List
import mariadb

# Import dei modelli e delle utility necessarie
from utils.models import ValutazioneCreate, ValutazioneOut
from utils.database import get_db_connection, close_db_resources

router = APIRouter(
    prefix="/valutazioni",
    tags=["Valutazioni"]
)

@router.post("", response_model=ValutazioneOut, status_code=status.HTTP_201_CREATED)
async def crea_valutazione(valutazione: ValutazioneCreate):
    """
    Permette a un paziente di creare una nuova valutazione per una prenotazione completata, quindi a visita effettuata.

    Logica di controllo:
    1. Verifica che la prenotazione esista.
    2. Verifica che lo stato della prenotazione sia 'Completata'.
    3. Verifica che l'utente che lascia la recensione sia lo stesso della prenotazione.
    4. Verifica che la prenotazione non sia già stata valutata.

    Args:
        valutazione (ValutazioneCreate): Dati per la nuova valutazione.

    Returns:
        ValutazioneOut: L'oggetto della valutazione creata.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Recupero dati della prenotazione per i controlli
        cursor.execute("SELECT * FROM Prenotazioni WHERE id = ?", (valutazione.prenotazione_id,))
        prenotazione = cursor.fetchone()

        if not prenotazione:
            raise HTTPException(status_code=404, detail="Prenotazione non trovata.")

        # Controlla se la prenotazione è stata completata
        if prenotazione['stato'] != 'Completata':
            raise HTTPException(
                status_code=403,
                detail="È possibile valutare solo le prenotazioni completate."
            )
        
        # Controlla che il paziente che valuta sia lo stesso della prenotazione
        if prenotazione['paziente_id'] != valutazione.paziente_id:
            raise HTTPException(
                status_code=403,
                detail="Non hai i permessi per valutare questa prenotazione."
            )

        # Inserisce la nuova valutazione. Il database lancerà un errore se la prenotazione_id è già stata usata (grazie al vincolo UNIQUE).
        query_insert = """
            INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query_insert, (
            valutazione.prenotazione_id,
            valutazione.paziente_id,
            valutazione.medico_id,
            valutazione.punteggio,
            valutazione.commento
        ))
        
        nuova_valutazione_id = cursor.lastrowid
        conn.commit()

        # Recupera e restituisce la valutazione appena creata
        cursor.execute("SELECT * FROM Valutazioni WHERE id = ?", (nuova_valutazione_id,))
        nuova_valutazione_data = cursor.fetchone()
        
        return ValutazioneOut(**nuova_valutazione_data)

    except mariadb.IntegrityError as e:
        # Questo errore scatta se si tenta di valutare due volte la stessa prenotazione
        if 'UNIQUE' in str(e) and 'prenotazione_id' in str(e):
             raise HTTPException(status_code=409, detail="Questa prenotazione è già stata valutata.")
        
        # Gestisce altri errori di integrità (es. medico_id o paziente_id non validi)
        raise HTTPException(status_code=400, detail=f"Errore nei dati forniti: {e}")
        
    except mariadb.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore del database: {e}")
    finally:
        close_db_resources(conn, cursor)

@router.get("/medico/{medico_id}", response_model=List[ValutazioneOut])
async def get_valutazioni_medico(medico_id: int):
    """
    Recupera la lista di tutte le valutazioni ricevute da uno specifico medico.

    Args:
        medico_id (int): L'ID del medico.

    Returns:
        List[ValutazioneOut]: Una lista di oggetti valutazione.
        
    Raises:
        HTTPException: Se il medico non viene trovato o per errori del database.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Controlla che il medico esista per dare un errore 404
        cursor.execute("SELECT id FROM Medici WHERE id = ?", (medico_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Medico non trovato.")

        # Query per selezionare tutte le valutazioni di un medico, ordinate dalla più recente.
        query = "SELECT * FROM Valutazioni WHERE medico_id = ? ORDER BY data_valutazione DESC"
        cursor.execute(query, (medico_id,))
        
        valutazioni = cursor.fetchall()
        return [ValutazioneOut(**v) for v in valutazioni]

    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero delle valutazioni: {e}"
        )
    finally:
        close_db_resources(conn, cursor)