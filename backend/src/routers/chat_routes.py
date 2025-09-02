# chat_routes.py
"""
Backend Chat Routes - Secure API Endpoints for LangGraph Chat System

Gestisce le richieste chat con autenticazione JWT e orchestrazione LangGraph.
Implementa thread isolation per sicurezza: ogni utente ha thread privati.

Architettura: FastAPI → JWT Auth → LangGraph Orchestrator → AI Response
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
import logging

from utils.auth import get_current_user, get_optional_current_user
from utils.models import ChatMessage, ChatResponse, UserOut
from chat.orchestrator import invoke_orchestrator, memory

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Backend - Chat (LangGraph)"],
)

@router.post("/message", response_model=ChatResponse)
async def handle_chat_message(
    chat_message: ChatMessage,  # Messaggio + session_id dal frontend proxy
    user: Optional[UserOut] = Depends(get_optional_current_user)  # Auth opzionale: può essere None
):
    """
    Endpoint principale per messaggi chat con LangGraph orchestration.
    
    Supporta sia utenti autenticati che non autenticati.
    Per utenti autenticati: thread privato con user ID
    Per utenti non autenticati: thread temporaneo solo con session ID
    
    Flusso: Optional JWT Auth → Thread ID Generation → LangGraph → AI Response
    """
    # Crea thread ID diverso in base allo stato di autenticazione
    if user:
        # Utente autenticato: thread privato con user ID
        thread_id = f"user_{user.id}_session_{chat_message.session_id}"
        logger.info(f"Processing authenticated message for thread {thread_id}: {chat_message.message[:50]}...")
    else:
        # Utente non autenticato: thread temporaneo solo con session ID
        thread_id = f"anonymous_session_{chat_message.session_id}"
        logger.info(f"Processing anonymous message for thread {thread_id}: {chat_message.message[:50]}...")
    
    try:
        # Invoca LangGraph orchestrator che gestisce agent + tools + memory
        # L'orchestrator mantiene la cronologia conversazione usando il thread_id
        answer = await invoke_orchestrator(thread_id, chat_message.message)
        
        return ChatResponse(
            response=answer,  # Risposta generata dall'AI tramite LangGraph
            session_id=chat_message.session_id,  # Mantiene coerenza con frontend
        )
        
    except Exception as e:
        logger.error(f"LangGraph orchestration failed for thread {thread_id}: {e}", exc_info=True)
        # Converte eccezioni interne in HTTP 500 con messaggio user-friendly
        # Non espone dettagli tecnici per sicurezza
        raise HTTPException(
            status_code=500,
            detail="Mi dispiace, si è verificato un errore tecnico. Riprova."
        )

@router.post("/reset", response_model=dict)
async def reset_chat_session(
    chat_message: ChatMessage,  # Richiede solo session_id, il campo message è ignorato
    user: Optional[UserOut] = Depends(get_optional_current_user)  # Auth opzionale
):
    """
    Reset completo della sessione chat: cancella tutta la cronologia conversazione.
    
    Supporta sia utenti autenticati che non autenticati.
    Utilizza LangGraph MemorySaver.delete_thread() per rimuovere completamente
    la memoria associata al thread, permettendo di ricominciare da zero.
    """
    # Genera thread ID basato sullo stato di autenticazione
    if user:
        thread_id = f"user_{user.id}_session_{chat_message.session_id}"
        logger.info(f"Chat reset requested for authenticated thread {thread_id}")
    else:
        thread_id = f"anonymous_session_{chat_message.session_id}"
        logger.info(f"Chat reset requested for anonymous thread {thread_id}")
    
    try:
        # Cancella completamente la cronologia conversazione dal MemorySaver LangGraph
        memory.delete_thread(thread_id)
        logger.info(f"Successfully deleted thread memory: {thread_id}")
        
        return {
            "message": "Chat reset successfully",  # Conferma operazione riuscita
            "thread_id": thread_id,  # ID thread cancellato (per debug)
            "session_id": chat_message.session_id  # Session ID per frontend
        }
        
    except Exception as e:
        logger.error(f"Errore nel reset per thread {thread_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Errore durante il reset della chat. Riprova."
        )
