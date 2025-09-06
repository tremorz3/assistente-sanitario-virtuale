"""
Questo modulo gestisce endpoint proxy per varie utilità, come
l'autocomplete degli indirizzi.
"""
from fastapi import APIRouter, Query

from utils.api_utils import public_call

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
    return public_call("GET", f"/api/autocomplete-address?query={query}")

@router.get("/specializzazioni")
async def proxy_get_specializzazioni():
    """
    Endpoint proxy che inoltra la richiesta per ottenere la lista
    delle specializzazioni al backend.
    """
    return public_call("GET", "/specializzazioni")

@router.get("/citta")
async def proxy_get_citta():
    """
    Endpoint proxy che inoltra la richiesta per ottenere la lista
    delle città disponibili al backend.
    """
    return public_call("GET", "/citta")
