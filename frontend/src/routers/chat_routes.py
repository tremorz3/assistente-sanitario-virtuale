from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from utils.models import APIParams, ChatRequestFromBrowser
from utils.api_client import call_api

router = APIRouter()
templates = Jinja2Templates(directory=os.getenv("TEMPLATES_DIR", "templates"))

@router.get("/", response_class=HTMLResponse)
def serve_chat_page(request: Request):
    """Serve la pagina HTML iniziale."""
    return templates.TemplateResponse("chat.html", {"request": request})

@router.post("/chat")
def proxy_chat_request(request: ChatRequestFromBrowser):
    """
    Riceve la richiesta dal browser e la inoltra all'API di logica
    usando la funzione helper centralizzata.
    """
    # Prepara il payload per l'API di logica
    payload_to_logic_api = {
        "domanda": request.domanda,
        "location": request.location
    }

    # Prepara i parametri per la funzione call_api
    api_params = APIParams(
        method="POST",
        endpoint="/chat",
        payload=payload_to_logic_api
    )
    
    # Chiama l'API di logica e restituisce il risultato al browser
    return call_api(params=api_params)

@router.post("/reset")
def proxy_reset_request():
    """
    Inoltra la richiesta di reset al backend di logica
    usando la funzione helper centralizzata.
    """
    # Prepara i parametri per la funzione call_api (senza payload)
    api_params = APIParams(
        method="POST",
        endpoint="/reset"
    )

    # Chiama l'API di logica e restituisce il risultato
    return call_api(params=api_params)