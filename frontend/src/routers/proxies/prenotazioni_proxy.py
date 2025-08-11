"""
Questo modulo gestisce tutti gli endpoint proxy relativi alla gestione
delle prenotazioni (creazione, visualizzazione, aggiornamento).
"""
from fastapi import APIRouter, Body, Header
from typing import Optional

from utils.models import APIParams
from utils.api_client import call_api

router = APIRouter(
    prefix="/api/prenotazioni",
    tags=["Frontend - Proxy Prenotazioni"]
)

@router.post("")
async def proxy_crea_prenotazione(payload: dict = Body(...), authorization: Optional[str] = Header(None)):
    """
    Endpoint proxy che inoltra la richiesta per creare una prenotazione al backend.
    """
    # Verifica se l'header Authorization è presente e ottiene il token
    token = authorization.split(" ")[1] if authorization else None
    
    api_params = APIParams(method="POST", endpoint="/prenotazioni", payload=payload)
    return call_api(params=api_params, token=token)

@router.get("/me")
async def proxy_get_my_prenotazioni(authorization: Optional[str] = Header(None)):
    """
    Proxy per ottenere le prenotazioni del paziente autenticato.
    """
    token = authorization.split(" ")[1] if authorization else None
    api_params = APIParams(method="GET", endpoint="/prenotazioni/paziente/me")
    return call_api(params=api_params, token=token)

@router.patch("/{prenotazione_id}")
async def proxy_update_prenotazione(prenotazione_id: int, payload: dict = Body(...), authorization: Optional[str] = Header(None)):
    """
    Proxy per aggiornare lo stato di una prenotazione.
    """
    token = authorization.split(" ")[1] if authorization else None
    api_params = APIParams(method="PATCH", endpoint=f"/prenotazioni/{prenotazione_id}", payload=payload)
    return call_api(params=api_params, token=token)

@router.get("/medico/me")
async def proxy_get_my_prenotazioni_medico(authorization: Optional[str] = Header(None)):
    """
    Proxy per ottenere le prenotazioni del medico autenticato.
    """
    token: Optional[str] = authorization.split(" ")[1] if authorization else None
    api_params: APIParams = APIParams(method="GET", endpoint="/prenotazioni/medico/me")
    return call_api(params=api_params, token=token)

