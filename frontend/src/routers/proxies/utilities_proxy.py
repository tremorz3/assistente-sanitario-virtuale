"""
Questo modulo gestisce endpoint proxy per varie utilità, come
l'autocomplete degli indirizzi.
"""
from fastapi import APIRouter, Query

from utils.models import APIParams
from utils.api_client import call_api

router = APIRouter(
    prefix="/api",
    tags=["Frontend - Proxy Utilities"]
)

@router.get("/autocomplete-address")
async def proxy_autocomplete_address(query: str = Query(..., min_length=3)):
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

@router.get("/specializzazioni")
async def proxy_get_specializzazioni():
    """
    Endpoint proxy che inoltra la richiesta per ottenere la lista
    delle specializzazioni al backend.
    """
    api_params = APIParams(method="GET", endpoint="/specializzazioni")
    return call_api(params=api_params)

@router.get("/citta")
async def proxy_get_citta():
    """
    Endpoint proxy che inoltra la richiesta per ottenere la lista
    delle città disponibili al backend.
    """
    api_params = APIParams(method="GET", endpoint="/citta")
    return call_api(params=api_params)