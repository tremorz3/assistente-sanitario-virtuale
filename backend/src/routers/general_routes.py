
from fastapi import APIRouter, HTTPException, status, Query
from typing import List
import mariadb

# Import dei modelli e delle utility necessari
from utils.models import SpecializzazioneOut, AddressSuggestion
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
        cursor.execute("SELECT * FROM Specializzazioni")
        specializzazioni = cursor.fetchall()
        return [SpecializzazioneOut(**spec) for spec in specializzazioni]
    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno durante il recupero delle specializzazioni."
        )
    finally:
        close_db_resources(conn, cursor)