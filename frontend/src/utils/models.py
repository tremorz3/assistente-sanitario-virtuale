from typing import Optional, Dict, Any
from pydantic import BaseModel

class APIParams(BaseModel):
    """
    Modello Pydantic per standardizzare i parametri delle chiamate API.
    """
    method: str  # Es. "POST", "GET"
    endpoint: str  # Nome dell'endpoint API da utilizzare
    payload: Optional[Dict[str, Any]] = None

class ChatRequestFromBrowser(BaseModel):
    """
    Modello Pydantic per i dati di chat ricevuti dal browser.
    """
    domanda: str
    location: Optional[Dict[str, float]] = None

