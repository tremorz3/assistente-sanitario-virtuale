import requests
import os
from fastapi import APIRouter, HTTPException, status

# Import dei modelli e delle utility necessari
from utils.models import Messaggio, RichiestaChat, RichiestaOllama, RispostaOllama
from utils.chat_setup import storico_chat, reset_chat

router = APIRouter(
    prefix="/chat",  # prefisso comune
    tags=["Chat AI"]
)

# Recupera la variabile d'ambiente una sola volta all'avvio del modulo
OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL")

@router.post("", response_model=Messaggio) # L'URL diventa /chat
def chat_con_ai(request: RichiestaChat):
    """
    Gestisce un singolo turno di chat. Riceve la domanda dell'utente,
    la arricchisce con informazioni di localizzazione, interroga il modello AI
    e restituisce la sua risposta.
    """
    contenuto_utente = request.domanda
    location_info = ""

    # Cerca di ottenere un contesto di localizzazione, dando priorità
    # alle coordinate precise fornite dal client.
    if request.location:
        # Se sono presenti coordinate precise, le formatta in una stringa.
        lat = request.location.get('lat')
        lon = request.location.get('lon')
        if lat is not None and lon is not None:
             location_info = f"\n[INFO POSIZIONE UTENTE: Lat={lat}, Lon={lon}]"
    elif request.client_ip:
        # Altrimenti, tenta un fallback usando l'IP per una posizione approssimativa.
        try:
            geo_response = requests.get(f"http://ip-api.com/json/{request.client_ip}")
            geo_data = geo_response.json()
            if geo_data.get("status") == "success":
                citta = geo_data.get("city", "N/A")
                regione = geo_data.get("regionName", "N/A")
                location_info = f"\n[INFO POSIZIONE APPROSSIMATIVA UTENTE: Città={citta}, Regione={regione}]"
        except requests.RequestException:
            # In caso di errore nella chiamata all'API di geolocalizzazione, prosegue senza.
            pass

    # Aggiunge le informazioni di posizione, se trovate, al messaggio dell'utente.
    if location_info:
        contenuto_utente += location_info
    
    # Aggiorna la cronologia della conversazione con il messaggio completo dell'utente.
    storico_chat.append(Messaggio(role="user", content=contenuto_utente))
    print(f"Messaggio utente: {contenuto_utente}")
    print(f"Storico chat attuale: {storico_chat}")
    
    # Prepara il payload per il modello AI, includendo l'intera cronologia.
    payload = RichiestaOllama(messages=storico_chat)
    
    try:
        # Invia la richiesta al servizio del modello AI (Ollama).
        response = requests.post(OLLAMA_API_URL, json=payload.model_dump(), timeout=180.0)
        response.raise_for_status()  # Solleva un'eccezione per errori HTTP (es. 4xx, 5xx).
        
        # Estrae, valida e aggiunge la risposta del modello allo storico.
        risposta_ollama = RispostaOllama(**response.json())
        messaggio_ai = risposta_ollama.message
        storico_chat.append(messaggio_ai)
        
        return messaggio_ai
    except requests.RequestException as e:
        # Gestisce errori di rete o di comunicazione con il servizio AI.
        raise HTTPException(status_code=503, detail=f"Errore di comunicazione con il modello AI: {e}")

@router.post("/reset") # L'URL completo sarà /chat/reset
def reset_chat_history():
    """
    Resetta la cronologia della chat chiamando la funzione dedicata.
    """
    reset_chat()
    return {"status": "success", "message": "Cronologia chat resettata."}


