
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional, Dict, Any
import mariadb
from pydantic import BaseModel

# Import dei modelli e delle utility necessari
from utils.models import (
    SpecializzazioneOut, 
    AddressSuggestion, 
    MedicoOut,
    MedicoGeolocalizzatoOut,
    UserOut,
    ChatMessage,
    ChatResponse
)
from utils.geocoding import get_address_suggestions
from utils.database import get_db_connection, close_db_resources
from utils.auth import get_current_user

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

@router.get("/citta", response_model=List[str])
async def get_citta_disponibili() -> List[str]:
    """
    Recupera l'elenco delle città dove sono presenti medici.
    Returns:
        List[str]: Lista delle città ordinate alfabeticamente.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT citta FROM Medici ORDER BY citta ASC")
        citta_list = [row[0] for row in cursor.fetchall()]
        return citta_list
    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore durante il recupero delle città."
        )
    finally:
        close_db_resources(conn, cursor)

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
    citta: Optional[str] = Query(None, description="Filtra i medici per città."),
    sort_by: Optional[str] = Query(None, description="Ordina i medici. Valori permessi: 'punteggio', 'cognome'."),
    date_disponibili: Optional[str] = Query(None, description="Filtra per date disponibili. Valori: 'oggi', '3_giorni'.")
) -> List[MedicoOut]:
    """
    (Pubblico) Recupera la lista di tutti i medici iscritti alla piattaforma
    con le loro informazioni principali, inclusa la specializzazione, con possibilità di filtro e ordinamento.
    Args:
        specializzazione_id (Optional[int]): ID della specializzazione per filtrare i medici.
        citta (Optional[str]): Nome della città per filtrare i medici.
        sort_by (Optional[str]): Criterio di ordinamento. Può essere 'punteggio' o 'cognome'. L'ordinamento predefinito è per punteggio.
        date_disponibili (Optional[str]): Filtro date disponibili. Valori: 'oggi', '3_giorni'.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query con JOIN per recuperare anche il nome della specializzazione
        base_query = """
            SELECT DISTINCT
                m.id, 
                m.nome, 
                m.cognome, 
                m.citta, 
                m.indirizzo_studio, 
                m.punteggio_medio,
                m.latitudine,
                m.longitudine,
                s.nome AS specializzazione_nome
            FROM Medici m
            JOIN Specializzazioni s ON m.specializzazione_id = s.id
        """
        
        # Lista per i parametri della query per prevenire SQL Injection
        params = []
        conditions = []
        
        # Aggiungi JOIN con Disponibilita se viene richiesto il filtro date
        if date_disponibili:
            base_query += " JOIN Disponibilita d ON m.id = d.medico_id"
            conditions.append("d.is_prenotato = FALSE")
        
        if specializzazione_id is not None:
            conditions.append("m.specializzazione_id = ?")
            params.append(specializzazione_id)
        
        if citta is not None:
            conditions.append("LOWER(m.citta) LIKE LOWER(?)")
            params.append(f"%{citta}%")
        
        # Filtro date disponibili
        if date_disponibili:
            if date_disponibili == "oggi":
                conditions.append("DATE(d.data_ora_inizio) = CURDATE()")
            elif date_disponibili == "3_giorni":
                conditions.append("d.data_ora_inizio BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)")
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

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

@router.get("/medici/vicini", response_model=List[MedicoGeolocalizzatoOut])
async def get_medici_vicini_pubblico(
    lat: float = Query(..., description="Latitudine del punto di ricerca."),
    lon: float = Query(..., description="Longitudine del punto di ricerca."),
    raggio_km: int = Query(20, description="Raggio di ricerca in chilometri.", ge=1, le=100),
    specializzazione_id: Optional[int] = Query(None, description="Filtra per specializzazione.")
) -> List[MedicoGeolocalizzatoOut]:
    """
    (Pubblico) Recupera una lista di medici entro un raggio specificato,
    ordinati per distanza crescente.

    Utilizza la formula di Haversine per calcolare la distanza geodetica
    tra due punti su una sfera (la Terra).

    Args:
        lat (float): Latitudine dell'utente.
        lon (float): Longitudine dell'utente.
        raggio_km (int): Raggio massimo di ricerca in km. Default 20.
        specializzazione_id (Optional[int]): ID della specializzazione per filtrare.

    Returns:
        List[MedicoGeolocalizzatoOut]: Una lista di medici con la loro distanza.
    """
    return await _search_nearby_doctors(lat, lon, raggio_km, specializzazione_id)

@router.get("/medici/vicini-autenticato", response_model=List[MedicoGeolocalizzatoOut])
async def get_medici_vicini_autenticato(
    lat: float = Query(..., description="Latitudine del punto di ricerca."),
    lon: float = Query(..., description="Longitudine del punto di ricerca."),
    raggio_km: int = Query(20, description="Raggio di ricerca in chilometri.", ge=1, le=100),
    specializzazione_id: Optional[int] = Query(None, description="Filtra per specializzazione."),
    current_user: UserOut = Depends(get_current_user)
) -> List[MedicoGeolocalizzatoOut]:
    """
    (Protetto) Recupera una lista di medici entro un raggio specificato per utenti autenticati,
    ordinati per distanza crescente.

    Args:
        lat (float): Latitudine dell'utente.
        lon (float): Longitudine dell'utente.
        raggio_km (int): Raggio massimo di ricerca in km. Default 20.
        specializzazione_id (Optional[int]): ID della specializzazione per filtrare.
        current_user (UserOut): Utente autenticato (iniettato da Depends).

    Returns:
        List[MedicoGeolocalizzatoOut]: Una lista di medici con la loro distanza.
    """
    if current_user.tipo_utente != 'paziente':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Azione non permessa. Solo i pazienti possono cercare medici vicini."
        )

    return await _search_nearby_doctors(lat, lon, raggio_km, specializzazione_id)


async def _search_nearby_doctors(
    lat: float, 
    lon: float, 
    raggio_km: int, 
    specializzazione_id: Optional[int] = None
) -> List[MedicoGeolocalizzatoOut]:
    """
    Funzione interna per cercare medici nelle vicinanze con filtri opzionali.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # La formula di Haversine implementata in SQL con filtro specializzazione opzionale
        # 6371 è il raggio medio della Terra in chilometri.
        haversine_query = """
            SELECT 
                m.id, m.nome, m.cognome, m.citta, 
                m.indirizzo_studio, m.punteggio_medio,
                s.nome AS specializzazione_nome,
                m.latitudine,
                m.longitudine,
                (
                    6371 * ACOS(
                        COS(RADIANS(?)) * COS(RADIANS(m.latitudine)) *
                        COS(RADIANS(m.longitudine) - RADIANS(?)) +
                        SIN(RADIANS(?)) * SIN(RADIANS(m.latitudine))
                    )
                ) AS distanza_km
            FROM Medici m
            JOIN Specializzazioni s ON m.specializzazione_id = s.id
        """
        
        # Parametri per la query: latitudine, longitudine, latitudine (per il seno)
        params = [lat, lon, lat]
        
        # Aggiunge filtro specializzazione se specificato
        if specializzazione_id is not None:
            haversine_query += " WHERE m.specializzazione_id = ?"
            params.append(specializzazione_id)
        
        haversine_query += """
            HAVING distanza_km <= ?
            ORDER BY distanza_km ASC
            LIMIT 50
        """
        params.append(raggio_km)
        
        cursor.execute(haversine_query, tuple(params))
        medici = cursor.fetchall()
        
        return [MedicoGeolocalizzatoOut(**m) for m in medici]

    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore del database durante la ricerca geolocalizzata: {e}"
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
                m.latitudine,
                m.longitudine,
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