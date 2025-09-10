"""
Questo modulo gestisce gli endpoint proxy per la creazione e cancellazione
delle disponibilità da parte di un medico autenticato.
"""
from typing import Optional

from fastapi import APIRouter, Body, Header

from utils.api_utils import authenticated_call

router = APIRouter(
    prefix="/api/disponibilita",
    tags=["Frontend - Proxy Disponibilità"]
)

@router.post("")
async def proxy_crea_disponibilita(
    payload: dict = Body(...),
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Proxy per inoltrare la richiesta di creazione di una nuova disponibilità al backend.
    Richiede autenticazione.
    """
    return authenticated_call("POST", "/disponibilita", authorization, payload)

@router.delete("/{disponibilita_id}")
async def proxy_cancella_disponibilita(
    disponibilita_id: int,
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Proxy per inoltrare la richiesta di cancellazione di una disponibilità al backend.
    Richiede autenticazione.
    """
    return authenticated_call("DELETE", f"/disponibilita/{disponibilita_id}", authorization)
