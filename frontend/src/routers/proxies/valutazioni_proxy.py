"""
Questo modulo gestisce gli endpoint proxy relativi alla creazione e
visualizzazione delle valutazioni.
"""
from fastapi import APIRouter, Body, Header
from typing import Optional

from utils.api_utils import authenticated_call

router = APIRouter(
    prefix="/api/valutazioni",
    tags=["Frontend - Proxy Valutazioni"]
)

@router.get("")
async def proxy_get_my_valutazioni(authorization: Optional[str] = Header(None)):
    """
    Proxy per ottenere le valutazioni del paziente autenticato.
    """
    return authenticated_call("GET", "/valutazioni/me", authorization)

@router.post("")
async def proxy_crea_valutazione(payload: dict = Body(...), authorization: Optional[str] = Header(None)):
    """
    Proxy per creare una nuova valutazione.
    """
    return authenticated_call("POST", "/valutazioni", authorization, payload)

@router.get("/medico/me")
async def proxy_get_my_valutazioni_medico(authorization: Optional[str] = Header(None)):
    """
    Proxy per ottenere le valutazioni che ha ricevuto il medico autenticato.
    """
    return authenticated_call("GET", "/valutazioni/medico/me", authorization)
