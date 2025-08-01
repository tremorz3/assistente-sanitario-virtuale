import os
from datetime import date
import requests
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="Assistente Virtuale Sanitario Web Server")

templates_dir = os.getenv("TEMPLATES_DIR", "../templates")
templates = Jinja2Templates(directory=templates_dir)
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001") 

class APIParams(BaseModel):
    """Modello Pydantic per standardizzare i parametri delle chiamate API."""
    method: str  # Es. "POST", "GET"
    endpoint: str  # Nome dell'endpoint API da utilizzare
    payload: Optional[Dict[str, Any]] = None

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


@app.get("/pagina-login", response_class=HTMLResponse)
async def get_login_page(request: Request, success:bool = False):
    '''
    Endpoint per mostrare la pagina di login.
    '''
    context = {"request": request, "error": None}
    if success:
        context["success_message"] = "Registrazione avvenuta con successo! Ora puoi effettuare il login."
    return templates.TemplateResponse("login.html", context)

@app.post("/pagina-login", response_class=HTMLResponse)
async def post_login_page(request: Request, email: str = Form(...), password: str = Form(...)):
    '''
    Endpoint per gestire i dati inviati dal form di login.
    Comunica con l'API per autenticare l'utente.
    '''
    try:
        #Preparazione dei parametri per la chiamata API
        login_params: APIParams = APIParams(
            method="POST",
            endpoint="/login",
            payload={"email": email, "password": password}
        )

        # Chiamata all'API per il login
        response = call_api(login_params)

        # Se il login ha successo, reindirizza alla pagina principale (TEMPORANEO)
        content: str = f"""
        <html>
            <head><title>Login Riuscito</title></head>
            <body>
                <h1>Login effettuato con successo!</h1>
                <p>Email di accesso: {email}</p>
                <p>Tipo di utente: {response.get('tipo_utente')}</p>
                <p>Token di accesso: {response.get('token')['access_token']}</p>
            </body>
        </html>
        """
        return HTMLResponse(content=content)
    except HTTPException as e:
        # In caso di errore, mostra la pagina di login con un messaggio di errore
        return templates.TemplateResponse("login.html", {"request": request, "error": e.detail})

@app.get("/pagina-registrazione-paziente", response_class=HTMLResponse)
async def get_patient_register_page(request: Request):
    '''
    Mostra la pagina di registrazione per il paziente.
    '''
    return templates.TemplateResponse("signup-paziente.html", {"request": request})

@app.post("/pagina-registrazione-paziente", response_class=HTMLResponse)
async def post_register_page(
    request: Request,
    nome: str = Form(...),
    cognome: str = Form(...),
    data_di_nascita: date = Form(...),
    telefono: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
) -> RedirectResponse:
    '''
    Gestisce la logica di registrazione di un paziente.
    Args:
        request (Request): Oggetto di richiesta FastAPI.
        nome (str): Nome del paziente.
        cognome (str): Cognome del paziente.
        data_di_nascita (date): Data di nascita del paziente.
        telefono (str): Numero di telefono del paziente.
        email (str): Indirizzo email del paziente.
        password (str): Password del paziente.
    Returns:
        RedirectResponse: Reindirizza alla pagina di login con un messaggio di successo o errore.
    Raises:
        HTTPException: Se una delle chiamate API fallisce o se i dati non sono validi.
    '''
    try:
        # Payload con tutti i dati richiesti dal backend
        patient_payload: Dict[str, Any] = {
            "nome": nome,
            "cognome": cognome,
            "data_di_nascita": data_di_nascita.isoformat(), # Conversione della data in formato ISO
            "telefono": telefono,
            "email": email,
            "password": password
        }
        
        # Parametri per la funzione helper
        register_params: APIParams = APIParams(
            method="POST",
            endpoint="/register/paziente",
            payload=patient_payload
        )

        call_api(register_params)
        
        return RedirectResponse(url="/pagina-login?success=true", status_code=303)

    except HTTPException as e:
        # Se la chiamata API fallisce (es. email già esistente), si mostra l'errore
        return templates.TemplateResponse("signup-paziente.html", {"request": request, "error": e.detail})

@app.get("/pagina-registrazione-medico", response_class=HTMLResponse)
async def get_medico_register_page(request: Request):
    '''
    Mostra la pagina di registrazione per il medico, recuperando dinamicamente
    la lista delle specializzazioni dall'API del backend.
    '''
    try:
        params = APIParams(method="GET", endpoint="/specializzazioni/")
        lista_specializzazioni = call_api(params)

        # Invio della lista al template
        context = {"request": request, "specializzazioni": lista_specializzazioni}
        return templates.TemplateResponse("signup-medico.html", context)

    except HTTPException as e:
        error_msg = f"Impossibile caricare le specializzazioni: {e.detail}"
        context = {"request": request, "error": error_msg}

        return templates.TemplateResponse("signup-medico.html", context)

@app.post("/pagina-registrazione-medico", response_class=HTMLResponse)
async def post_medico_register_page(
    request: Request,
    nome: str = Form(...),
    cognome: str = Form(...),
    citta: str = Form(...),
    telefono: str = Form(...),
    specializzazione_id: int = Form(...),
    ordine_iscrizione: str = Form(...),
    numero_iscrizione: str = Form(...),
    provincia_iscrizione: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
) -> RedirectResponse:
    '''
    Gestisce la logica di registrazione di un medico.
    Args:
        request (Request): Oggetto di richiesta FastAPI.
        nome (str): Nome del medico.
        cognome (str): Cognome del medico.  
        citta (str): Città del medico.
        telefono (str): Numero di telefono del medico.
        specializzazione_id (int): ID della specializzazione del medico.
        ordine_iscrizione (str): Numero di iscrizione all'ordine del medico.
        numero_iscrizione (str): Numero di iscrizione del medico.
        provincia_iscrizione (str): Provincia di iscrizione del medico.
        email (str): Email del medico.
        password (str): Password del medico.
    Returns:
        RedirectResponse: Reindirizza alla pagina di login con un messaggio di successo o errore.
    Raises:
        HTTPException: Se una delle chiamate API fallisce o se i dati non sono validi.
    '''
    try:
        # Il payload da inviare al backend
        medico_payload = {
            "nome": nome,
            "cognome": cognome,
            "citta": citta,
            "telefono": telefono,
            "specializzazione_id": specializzazione_id,
            "ordine_iscrizione": ordine_iscrizione,
            "numero_iscrizione": numero_iscrizione,
            "provincia_iscrizione": provincia_iscrizione,
            "email": email,
            "password": password
        }
        
        register_params = APIParams(
            method="POST",
            endpoint="/register/medico",
            payload=medico_payload
        )

        call_api(register_params)
        
        return RedirectResponse(url="/pagina-login?success=true", status_code=303)

    except HTTPException as e:
        # Se fallisce, ricarica le specializzazioni per mostrare di nuovo il form
        try:
            params = APIParams(method="GET", endpoint="/specializzazioni/")
            lista_specializzazioni = call_api(params)
        except HTTPException:
            lista_specializzazioni = []

        context = {
            "request": request, 
            "error": e.detail, 
            "specializzazioni": lista_specializzazioni
        }
        return templates.TemplateResponse("signup-medico.html", context)