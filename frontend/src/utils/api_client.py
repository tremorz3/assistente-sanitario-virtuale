import os
import requests
from typing import Optional, Dict, Any
from fastapi import HTTPException
from .models import APIParams

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")

def call_api(params: APIParams, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Funzione helper per gestire le chiamate all'API backend usando requests. Supporta chiamate autenticate tramite token JWT.
    Args:
        params (APIParams): Parametri della chiamata API, inclusi metodo, endpoint e payload.
        token (Optional[str]): Token JWT per l'autenticazione, se necessario.
    Returns:
        Dict[str, Any]: Risposta dell'API in formato JSON.
    Raises:
        HTTPException: Se la chiamata all'API fallisce o restituisce un errore.
    """
    # Costruzione dell'URL completo dell'API
    full_url = f"{API_BASE_URL.rstrip('/')}/{params.endpoint.lstrip('/')}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.request(
            method=params.method,
            url=full_url,
            json=params.payload,
            headers=headers
        )
        
        # Se la risposta è un errore (es. 401, 404, 500), solleva un'eccezione
        response.raise_for_status()
        
        # Risultato in formato JSON
        return response.json() if response.content else {}

    except requests.exceptions.HTTPError as e:
        # Estrazione del dettaglio dell'errore dal corpo della risposta, se presente
        error_detail = "Si è verificato un errore."
        try:
            error_detail = e.response.json().get("detail", error_detail)
        except Exception:
            pass # Se il parsing fallisce, mantiene il messaggio di errore generico
        raise HTTPException(status_code=e.response.status_code, detail=error_detail)

    except requests.exceptions.RequestException as e:
        # Errore di connessione o di rete
        raise HTTPException(status_code=503, detail=f"Errore di comunicazione con l'API: {e}")
