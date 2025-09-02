"""
Proxy Chat Endpoints - Frontend to Backend Communication

Questo modulo funge da ponte tra il browser e il backend API, gestendo:
1. Trasformazione dei formati dati (browser ↔ backend)
2. Inoltro sicuro delle richieste con autenticazione JWT 
3. Mappatura degli endpoint e gestione degli errori

Il proxy è necessario per evitare problemi CORS e centralizzare la logica di comunicazione.
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from utils.models import APIParams, ChatMessage, ChatResponse, ChatRequestFromBrowser, ChatResponseToBrowser
from utils.api_client import call_api

router = APIRouter(
    tags=["Frontend - Proxy Chat"]
)

@router.post("/chat/message", response_model=ChatResponseToBrowser)
async def proxy_chat_message(request: ChatRequestFromBrowser, authorization: Optional[str] = Header(None)):
    """
    Proxy per messaggi chat: trasforma formato browser → backend → browser.
    
    Flusso:
    1. Riceve ChatRequestFromBrowser (array messaggi + session_id)
    2. Estrae ultimo messaggio utente (il backend processa solo quello)
    3. Converte a ChatMessage backend (message + session_id)
    4. Inoltra al backend con JWT token
    5. Trasforma risposta backend a formato browser
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Nessun messaggio da inviare.")

    # Il backend processa un messaggio alla volta, estraiamo l'ultimo (il nuovo input)
    user_message = request.messages[0].content

    # Trasforma dal formato browser al formato backend API
    chat_message = ChatMessage(
        message=user_message,  # Contenuto del messaggio utente
        session_id=request.session_id  # Mantiene coerenza sessione
    )

    # Costruisce la chiamata API verso il backend
    api_params = APIParams(
        method="POST",
        endpoint="/chat/message",  # Endpoint backend LangGraph
        payload=chat_message.model_dump()  # Serializza a dict per HTTP
    )
    
    # Estrae JWT token dall'header Authorization (formato: "Bearer <token>")
    # Se non c'è token, invia None (per utenti non autenticati)
    token = authorization.split(" ")[1] if authorization and " " in authorization else None
    response_data = call_api(api_params, token)
    
    # Trasforma risposta backend ("response" field) → browser ("content" field)
    return ChatResponseToBrowser(
        content=response_data.get("response", ""),
        session_id=response_data.get("session_id", "")
    )

@router.post("/chat/reset", response_model=dict)
async def proxy_reset_chat(request: ChatRequestFromBrowser, authorization: Optional[str] = Header(None)):
    """
    Proxy per reset sessione chat: pulisce la memoria conversazione nel backend.
    
    Cancella completamente la cronologia della conversazione per il thread utente,
    permettendo di ricominciare una nuova conversazione da zero.
    """
    # Il backend richiede ChatMessage anche per reset, ma usa solo session_id
    chat_message = ChatMessage(
        message="",  # Campo obbligatorio ma ignorato dal backend per operazioni reset
        session_id=request.session_id  # Identifica quale thread cancellare
    )
    
    api_params = APIParams(
        method="POST",
        endpoint="/chat/reset",
        payload=chat_message.model_dump()
    )
    token = authorization.split(" ")[1] if authorization and " " in authorization else None
    response_data = call_api(api_params, token)
    return response_data