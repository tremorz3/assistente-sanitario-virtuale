from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Literal
import requests

# Per i messaggi che inviamo (sia utente che AI)
class MessaggioInviato(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

# Per l'intera richiesta che inviamo a Ollama
class RichiestaOllama(BaseModel):
    model: str = "alibayram/medgemma:4b"
    messages: List[MessaggioInviato]
    stream: bool = False 

# Per l'oggetto 'message' annidato che RICEVIAMO da Ollama
class MessaggioRicevuto(BaseModel):
    role: Literal["assistant"]
    content: str

# Per l'intera risposta che RICEVIAMO da Ollama
class RispostaOllama(BaseModel):
    message: MessaggioRicevuto # 'message' è un singolo oggetto, non una lista

def leggi_prompt_da_file(percorso_file: str) -> str:
    """Legge il contenuto di un file di testo."""
    with open(percorso_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

PROMPT_DI_SISTEMA = leggi_prompt_da_file("prompt.txt")

# Inizializza lo storico con il prompt di sistema come primo messaggio
storico_chat: List[MessaggioInviato] = [
    MessaggioInviato(role="system", content=PROMPT_DI_SISTEMA)
]

# Configurazione di FastAPI
app = FastAPI()
# Assicurati di avere una cartella 'templates' nella stessa directory di questo file.
templates = Jinja2Templates(directory="templates")
OLLAMA_API_URL = "http://localhost:11434/api/chat"


@app.post("/chat")
def chat_con_ollama(request: Request, domanda: str = Form(...)):
    """
    Gestisce una nuova domanda, aggiorna lo storico e ricarica la pagina.
    """
    # Aggiungi il messaggio dell'utente allo storico come MessaggioInviato
    messaggio_utente = MessaggioInviato(role="user", content=domanda)
    storico_chat.append(messaggio_utente)

    # Prepara il payload per Ollama con lo storico che contiene solo MessaggioInviato
    payload = RichiestaOllama(messages=storico_chat)
    
    # Invia la richiesta a Ollama
    response = requests.post(OLLAMA_API_URL, json=payload.model_dump(), timeout=180.0)
    response.raise_for_status()
    
    # Valida la risposta usando i modelli corretti
    risposta_ollama = RispostaOllama(**response.json())
    
    # Estrai l'oggetto MessaggioRicevuto
    messaggio_ai_ricevuto = risposta_ollama.message
    
    # Converti il MessaggioRicevuto in un MessaggioInviato per coerenza
    messaggio_per_storico = MessaggioInviato(
        role=messaggio_ai_ricevuto.role, 
        content=messaggio_ai_ricevuto.content
    )
    # Aggiungi allo storico solo oggetti di tipo MessaggioInviato
    storico_chat.append(messaggio_per_storico)
    
    # Rendi di nuovo il template, passando l'intero storico aggiornato
    # return templates.TemplateResponse("index.html", {"request": request, "storico": storico_chat})
    return messaggio_per_storico # solo per test

# Sostituisci la vecchia funzione /reset con questa
@app.post("/reset")
def reset_chat(request: Request):
    """
    Endpoint per resettare la cronologia della chat, mantenendo il prompt di sistema.
    """
    storico_chat.clear()
    storico_chat.append(MessaggioInviato(role="system", content=PROMPT_DI_SISTEMA))
    return # templates.TemplateResponse("index.html", {"request": request, "storico": storico_chat})