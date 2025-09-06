"""
Questo modulo gestisce tutti gli endpoint proxy relativi alla gestione
delle prenotazioni (creazione, visualizzazione, aggiornamento).
"""
from fastapi import APIRouter, Body, Header
from typing import Optional

from utils.api_utils import authenticated_call

router = APIRouter(
    prefix="/api/prenotazioni",
    tags=["Frontend - Proxy Prenotazioni"]
)

@router.post("")
async def proxy_crea_prenotazione(payload: dict = Body(...), authorization: Optional[str] = Header(None)):
    """
    Endpoint proxy che inoltra la richiesta per creare una prenotazione al backend.
    """
    return authenticated_call("POST", "/prenotazioni", authorization, payload)

@router.get("/me")
async def proxy_get_my_prenotazioni(authorization: Optional[str] = Header(None)):
    """
    Proxy per ottenere le prenotazioni del paziente autenticato.
    """
    return authenticated_call("GET", "/prenotazioni/paziente/me", authorization)

@router.patch("/{prenotazione_id}")
async def proxy_update_prenotazione(prenotazione_id: int, payload: dict = Body(...), authorization: Optional[str] = Header(None)):
    """
    Proxy per aggiornare lo stato di una prenotazione.
    """
    return authenticated_call("PATCH", f"/prenotazioni/{prenotazione_id}", authorization, payload)

@router.get("/medico/me")
async def proxy_get_my_prenotazioni_medico(authorization: Optional[str] = Header(None)):
    """
    Proxy per ottenere le prenotazioni del medico autenticato.
    """
    return authenticated_call("GET", "/prenotazioni/medico/me", authorization)
