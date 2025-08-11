"""
Questo modulo gestisce gli endpoint proxy relativi alla creazione e
visualizzazione delle valutazioni.
"""
from fastapi import APIRouter, Body, Header
from typing import Optional

from utils.models import APIParams
from utils.api_client import call_api

router = APIRouter(
    prefix="/api/valutazioni",
    tags=["Frontend - Proxy Valutazioni"]
)

@router.get("")
async def proxy_get_my_valutazioni(authorization: Optional[str] = Header(None)):
    """
    Proxy per ottenere le valutazioni del paziente autenticato.
    """
    token = authorization.split(" ")[1] if authorization else None
    api_params = APIParams(method="GET", endpoint="/valutazioni/me")
    return call_api(params=api_params, token=token)

@router.post("")
async def proxy_crea_valutazione(payload: dict = Body(...), authorization: Optional[str] = Header(None)):
    """
    Proxy per creare una nuova valutazione.
    """
    token = authorization.split(" ")[1] if authorization else None
    api_params = APIParams(method="POST", endpoint="/valutazioni", payload=payload)
    return call_api(params=api_params, token=token)

