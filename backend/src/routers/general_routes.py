
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
import mariadb

# Import dei modelli e delle utility necessari
from utils.models import SpecializzazioneOut, AddressSuggestion, MedicoOut
from utils.geocoding import get_address_suggestions
from utils.database import get_db_connection, close_db_resources

router = APIRouter(
    tags=["Utilities & Dati Generali"] # Un tag per raggruppare questi endpoint
)

@router.get("/api/autocomplete-address", response_model=List[AddressSuggestion])
async def autocomplete_address(query: str = Query(..., min_length=3)):
    """
    Fornisce suggerimenti di indirizzi per l'autocomplete.
    """
    suggestions = get_address_suggestions(query)
    return suggestions

@router.get("/specializzazioni", response_model=List[SpecializzazioneOut])
async def get_specializzazioni() -> List[SpecializzazioneOut]:
    '''
    Recupera tutte le specializzazioni dal database.
    Returns:
        List[SpecializzazioneOut]: Lista di oggetti SpecializzazioneOut.
    Raises:
        HTTPException: Se si verifica un errore durante il recupero delle specializzazioni.
    '''
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Specializzazioni ORDER BY nome ASC")
        specializzazioni = cursor.fetchall()
        return [SpecializzazioneOut(**spec) for spec in specializzazioni]
    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno durante il recupero delle specializzazioni."
        )
    finally:
        close_db_resources(conn, cursor)

@router.get("/medici", response_model=List[MedicoOut])
async def get_lista_medici(
    specializzazione_id: Optional[int] = Query(None, description="Filtra i medici per ID di specializzazione."),
    sort_by: Optional[str] = Query(None, description="Ordina i medici. Valori permessi: 'punteggio', 'cognome'.")
) -> List[MedicoOut]:
    """
    (Pubblico) Recupera la lista di tutti i medici iscritti alla piattaforma
    con le loro informazioni principali, inclusa la specializzazione, con possibilità di filtro e ordinamento.
    Args:
        specializzazione_id (Optional[int]): ID della specializzazione per filtrare i medici.
        sort_by (Optional[str]): Criterio di ordinamento. Può essere 'punteggio' o 'cognome'. L'ordinamento predefinito è per punteggio.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query con JOIN per recuperare anche il nome della specializzazione
        base_query = """
            SELECT 
                m.id, 
                m.nome, 
                m.cognome, 
                m.citta, 
                m.indirizzo_studio, 
                m.punteggio_medio,
                s.nome AS specializzazione_nome
            FROM Medici m
            JOIN Specializzazioni s ON m.specializzazione_id = s.id
        """
        # Lista per i parametri della query per prevenire SQL Injection
        params = []
        if specializzazione_id is not None:
            base_query += " WHERE m.specializzazione_id = ?"
            params.append(specializzazione_id)

        # Aggiungiamo la clausola ORDER BY in base al parametro sort_by
        # Usiamo un approccio "whitelist" per sicurezza, accettando solo valori noti.
        if sort_by == 'cognome':
            base_query += " ORDER BY m.cognome ASC, m.nome ASC"
        else:
            # Default: ordina per punteggio (o se sort_by == 'punteggio')
            base_query += " ORDER BY m.punteggio_medio DESC, m.cognome ASC"

        cursor.execute(base_query, tuple(params))
        
        medici = cursor.fetchall()
        return [MedicoOut(**m) for m in medici]

    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero della lista dei medici: {e}"
        )
    finally:
        close_db_resources(conn, cursor)

@router.get("/medici/{medico_id}", response_model=MedicoOut)
async def get_dettaglio_medico(medico_id: int):
    """
    (Pubblico) Recupera i dettagli di un singolo medico, inclusa la sua
    specializzazione.
    
    Args:
        medico_id (int): L'ID del medico da recuperare.

    Returns:
        MedicoOut: Un oggetto con i dati del medico.
        
    Raises:
        HTTPException: Se il medico con l'ID specificato non viene trovato.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query con JOIN simile a quella per la lista, ma filtrata per un ID specifico.
        query = """
            SELECT 
                m.id, 
                m.nome, 
                m.cognome, 
                m.citta, 
                m.indirizzo_studio, 
                m.punteggio_medio,
                s.nome AS specializzazione_nome
            FROM Medici m
            JOIN Specializzazioni s ON m.specializzazione_id = s.id
            WHERE m.id = ?
        """
        cursor.execute(query, (medico_id,))
        
        medico = cursor.fetchone()
        
        # Se la query non restituisce risultati, il medico non esiste.
        if not medico:
            raise HTTPException(status_code=404, detail="Medico non trovato.")
            
        return MedicoOut(**medico)

    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nel recupero del medico: {e}"
        )
    finally:
        close_db_resources(conn, cursor)