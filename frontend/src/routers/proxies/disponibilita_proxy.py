"""
Questo modulo gestisce gli endpoint proxy per la creazione e cancellazione
delle disponibilità da parte di un medico autenticato.
"""
from typing import Optional

from fastapi import APIRouter, Body, Header

from utils.api_client import call_api
from utils.models import APIParams

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
    token: Optional[str] = authorization.split(" ")[1] if authorization else None
    api_params: APIParams = APIParams(method="POST", endpoint="/disponibilita", payload=payload)
    return call_api(params=api_params, token=token)

@router.delete("/{disponibilita_id}")
async def proxy_cancella_disponibilita(
    disponibilita_id: int,
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Proxy per inoltrare la richiesta di cancellazione di una disponibilità al backend.
    Richiede autenticazione.
    """
    token: Optional[str] = authorization.split(" ")[1] if authorization else None
    api_params: APIParams = APIParams(method="DELETE", endpoint=f"/disponibilita/{disponibilita_id}")
    return call_api(params=api_params, token=token)
