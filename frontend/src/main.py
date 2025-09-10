"""
File principale dell'applicazione frontend FastAPI.

Questo file inizializza l'applicazione e registra tutti i router necessari
per servire le viste HTML e per fare da proxy alle chiamate API verso il backend.
La nuova struttura modulare importa i router da posizioni specifiche:
- `routers.views`: Contiene tutti gli endpoint che restituiscono pagine HTML.
- `routers.proxies.*`: Contengono gli endpoint che comunicano con il backend.
"""
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from routers import views
from routers.proxies import (
    auth_proxy,
    chat_proxy,
    disponibilita_proxy,
    utilities_proxy,
    medici_proxy,
    prenotazioni_proxy,
    valutazioni_proxy
)

app = FastAPI(title="Assistente Virtuale Sanitario Web Server")
# Monta la cartella "static" per servire file statici come CSS, JavaScript e immagini
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# Includiamo i router nell'applicazione principale
app.include_router(views.router)
app.include_router(auth_proxy.router)
app.include_router(chat_proxy.router)
app.include_router(disponibilita_proxy.router)
app.include_router(utilities_proxy.router)
app.include_router(medici_proxy.router)
app.include_router(prenotazioni_proxy.router)
app.include_router(valutazioni_proxy.router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Endpoint per gestire la richiesta automatica del favicon da parte del browser
    e prevenire errori 404 nella console.
    """
    # Restituiamo una risposta 204 No Content, che è il modo corretto
    # per dire al browser "Ok, ho ricevuto la richiesta, ma non ho nulla da inviare".
    return Response(status_code=204)