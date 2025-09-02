"""
Questo modulo gestisce gli endpoint proxy per recuperare informazioni
sui medici, come la lista completa, i dettagli di un singolo medico
e le loro disponibilità.
"""
from fastapi import APIRouter, Request, Header, Query
from typing import Optional

from utils.models import APIParams
from utils.api_client import call_api

router = APIRouter(
    prefix="/medici/api",  # Un prefisso comune per le API relative ai medici
    tags=["Frontend - Proxy Medici"]
)

@router.get("/list")
async def proxy_get_lista_medici(request: Request):
    """
    Endpoint proxy che chiama il backend per recuperare la lista completa dei medici
    e la restituisce come JSON.
    """
    query_params = request.query_params

    backend_endpoint = "/medici"
    if query_params:
        backend_endpoint += f"?{query_params}"

    api_params = APIParams(method="GET", endpoint=backend_endpoint)
    return call_api(params=api_params)

@router.get("/vicini")
async def proxy_get_medici_vicini(
    lat: float,
    lon: float,
    raggio_km: int = 20,
    specializzazione_id: Optional[int] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Proxy per inoltrare la richiesta di ricerca al backend di medici vicini.
    Richiede autenticazione.
    """
    token = authorization.split(" ")[1] if authorization else None
    
    backend_endpoint = f"/medici/vicini?lat={lat}&lon={lon}&raggio_km={raggio_km}"
    if specializzazione_id:
        backend_endpoint += f"&specializzazione_id={specializzazione_id}"
    
    api_params = APIParams(method="GET", endpoint=backend_endpoint)
    return call_api(params=api_params, token=token)


@router.get("/{medico_id}/details")
async def proxy_get_dettaglio_medico(medico_id: int):
    """
    Endpoint proxy che chiama il backend per recuperare i dettagli
    di un singolo medico.
    """
    api_params = APIParams(method="GET", endpoint=f"/medici/{medico_id}")
    return call_api(params=api_params)

@router.get("/{medico_id}/disponibilita")
async def proxy_get_disponibilita_medico(medico_id: int, solo_libere: bool = True):
    """
    Endpoint proxy che inoltra la richiesta per ottenere le disponibilità 
    di un medico al backend.
    """
    # Costruiamo l'endpoint del backend, includendo il parametro query 'solo_libere'
    backend_endpoint = f"/disponibilita/medici/{medico_id}?solo_libere={solo_libere}"
    
    api_params = APIParams(method="GET", endpoint=backend_endpoint)
    
    # La nostra funzione call_api si occuperà di chiamare il backend e restituire i dati
    return call_api(params=api_params)