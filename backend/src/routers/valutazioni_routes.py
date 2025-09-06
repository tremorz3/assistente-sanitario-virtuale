from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
import mariadb

# Import dei modelli, delle utility e della dipendenza di sicurezza
from utils.models import ValutazioneCreate, ValutazioneOut
from utils.database_manager import db_transaction, db_readonly
from utils.auth_decorators import get_paziente_profile_id, get_medico_profile_id

router = APIRouter(
    prefix="/valutazioni",
    tags=["Valutazioni"]
)

@router.post("", response_model=ValutazioneOut, status_code=status.HTTP_201_CREATED)
async def crea_valutazione(valutazione: ValutazioneCreate, paziente_id: int = Depends(get_paziente_profile_id)) -> ValutazioneOut:
    """
    Permette a un paziente di creare una nuova valutazione per una prenotazione completata, quindi a visita effettuata.

    Args:
        valutazione (ValutazioneCreate): Dati per la nuova valutazione.

    Returns:
        ValutazioneOut: L'oggetto della valutazione creata.
    Raises:
        HTTPException: Se la prenotazione non esiste, non è completata, o se il paziente non ha i permessi per valutare.
    """
    try:
        with db_transaction() as (conn, cursor):
            # Recupero dati della prenotazione per i controlli di autorizzazione
            query_prenotazione = """
                SELECT p.id, p.stato, p.paziente_id, d.medico_id
                FROM Prenotazioni p
                JOIN Disponibilita d ON p.disponibilita_id = d.id
                WHERE p.id = ?
            """
            cursor.execute(query_prenotazione, (valutazione.prenotazione_id,))
            prenotazione = cursor.fetchone()

            if not prenotazione:
                raise HTTPException(status_code=404, detail="Prenotazione non trovata.")

            # Controlli di autorizzazione
            if prenotazione['stato'] != 'Completata':
                raise HTTPException(status_code=403, detail="È possibile valutare solo le prenotazioni completate.")
            
            if prenotazione['paziente_id'] != paziente_id:
                raise HTTPException(status_code=403, detail="Azione non permessa. Non puoi valutare una prenotazione di un altro utente.")

            medico_id_da_valutare = prenotazione['medico_id']

            # Inserisce la nuova valutazione. Il database lancerà un errore se la prenotazione_id è già stata usata (grazie al vincolo UNIQUE).
            query_insert = """
                INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(query_insert, (
                valutazione.prenotazione_id,
                paziente_id,
                medico_id_da_valutare,
                valutazione.punteggio,
                valutazione.commento
            ))
            
            nuova_valutazione_id = cursor.lastrowid
            # Commit automatico nel context manager

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
        # db_transaction ha già gestito rollback; rilancia come 500 generico
        raise HTTPException(status_code=500, detail="Errore del database durante la creazione della valutazione")

@router.get("/me", response_model=List[ValutazioneOut])
async def get_my_valutazioni(paziente_id: int = Depends(get_paziente_profile_id)) -> List[ValutazioneOut]:
    """
    (Protetto) Recupera la lista di tutte le valutazioni lasciate dal paziente autenticato.
    Args:
        current_user (UserOut): L'utente autenticato, ottenuto tramite la dipendenza get_current_user.
    Returns:
        List[ValutazioneOut]: Una lista di oggetti valutazione lasciate dal paziente loggato.
    Raises:
        HTTPException: Se l'utente non è un paziente o se si verifica un errore nel database.
    """
    with db_readonly() as cursor:
        # Query per selezionare tutte le valutazioni di quel paziente
        query = "SELECT * FROM Valutazioni WHERE paziente_id = ?"
        cursor.execute(query, (paziente_id,))
        valutazioni = cursor.fetchall()
        return [ValutazioneOut(**v) for v in valutazioni]

@router.get("/medico/me", response_model=List[ValutazioneOut])
async def get_my_valutazioni_medico(medico_id: int = Depends(get_medico_profile_id)) -> List[ValutazioneOut]:
    """
    (Protetto) Recupera la lista di tutte le valutazioni ricevute dal medico autenticato.
    """
    with db_readonly() as cursor:
        # Query per selezionare tutte le valutazioni di quel medico, ordinate dalla più recente.
        query = "SELECT * FROM Valutazioni WHERE medico_id = ? ORDER BY data_valutazione DESC"
        cursor.execute(query, (medico_id,))
        valutazioni = cursor.fetchall()
        return [ValutazioneOut(**v) for v in valutazioni]

@router.get("/medico/{medico_id}", response_model=List[ValutazioneOut])
async def get_valutazioni_medico(medico_id: int) -> List[ValutazioneOut]:
    """
    (Endpoint pubblico) Recupera la lista di tutte le valutazioni ricevute da uno specifico medico.

    Args:
        medico_id (int): L'ID del medico.

    Returns:
        List[ValutazioneOut]: Una lista di oggetti valutazione.
        
    Raises:
        HTTPException: Se il medico non viene trovato o per errori del database.
    """
    with db_readonly() as cursor:
        # Controlla che il medico esista per dare un errore 404
        cursor.execute("SELECT id FROM Medici WHERE id = ?", (medico_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Medico non trovato.")

        # Query per selezionare tutte le valutazioni di un medico, ordinate dalla più recente.
        query = "SELECT * FROM Valutazioni WHERE medico_id = ? ORDER BY data_valutazione DESC"
        cursor.execute(query, (medico_id,))
        valutazioni = cursor.fetchall()
        return [ValutazioneOut(**v) for v in valutazioni]
