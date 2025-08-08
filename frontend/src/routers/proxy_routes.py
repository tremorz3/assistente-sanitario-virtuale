from fastapi import APIRouter, Query

from utils.models import APIParams
from utils.api_client import call_api

router = APIRouter(
    prefix="/api", # Aggiungiamo un prefisso per coerenza
    tags=["API Proxy"]
)

@router.get("/api/autocomplete-address")
def proxy_autocomplete_address(query: str = Query(..., min_length=3)):
    """
    Endpoint proxy che inoltra la richiesta di autocomplete al backend
    e restituisce i suggerimenti al client.
    """
    # Prepara i parametri per la funzione helper che chiama il backend
    api_params = APIParams(
        method="GET",
        endpoint=f"/api/autocomplete-address?query={query}" # Passiamo la query all'endpoint del backend
    )

    # Chiama l'API di logica e restituisce il risultato al browser
    return call_api(params=api_params)
