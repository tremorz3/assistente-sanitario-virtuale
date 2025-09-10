# frontend/src/utils/models.py
"""
Modelli Pydantic per la gestione dei dati nel frontend.
Definisc e i modelli di trasformazione tra il formato del browser e il backend API.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class APIParams(BaseModel):
    """
    Standardizza i parametri per le chiamate API verso il backend.
    Utilizzato dal client API per costruire richieste HTTP uniformi.
    """
    method: str  # HTTP method (GET, POST, etc.)
    endpoint: str  # Endpoint relativo (es. "/chat/message")
    payload: Optional[Dict[str, Any]] = None  # Dati da inviare nel body

# --- Modelli Chat Condivisi ---
# Questi modelli devono essere identici a quelli del backend per garantire compatibilità API

class ChatMessage(BaseModel):
    """
    Schema per i messaggi inviati alla chat AI.
    Deve essere identico al modello backend per compatibilità API.
    """
    message: str = Field(..., description="Il messaggio dell'utente da inviare al chatbot.")
    session_id: str = Field(..., description="ID della sessione di conversazione.")

class ChatResponse(BaseModel):
    """
    Schema per le risposte del chatbot AI.
    Deve essere identico al modello backend per compatibilità API.
    """
    response: str = Field(..., description="La risposta generata dal chatbot.")
    session_id: str = Field(..., description="ID della sessione di conversazione.")

# --- Modelli Frontend Specifici per Browser ---
# Questi modelli gestiscono la trasformazione tra il formato atteso dal browser
# e quello richiesto dal backend API.

class ChatMessageFromBrowser(BaseModel):
    """
    Rappresenta un singolo messaggio nel formato atteso dal browser.
    Segue il pattern standard chat UI con ruolo (user/assistant) + contenuto.
    """
    role: str  # "user" o "assistant" per identificare chi ha scritto il messaggio
    content: str  # Testo del messaggio

class ChatRequestFromBrowser(BaseModel):
    """
    Richiesta di chat dal browser, contiene array di messaggi + session ID.
    Questo formato consente di inviare cronologia conversazione se necessario,
    anche se attualmente il backend processa solo il messaggio più recente.
    """
    session_id: str  # Identifica la conversazione per mantenere il contesto
    messages: List[ChatMessageFromBrowser]  # Array di messaggi (ultimo = nuovo input utente)

class ChatResponseToBrowser(BaseModel):
    """
    Risposta semplificata per il browser dopo trasformazione dal backend.
    Converte ChatResponse backend (con 'response') a formato browser (con 'content').
    """
    content: str = Field(..., description="Risposta testuale generata dall'AI")
    session_id: str = Field(..., description="ID sessione per continuità conversazione")
