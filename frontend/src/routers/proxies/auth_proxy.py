"""
Questo modulo gestisce tutti gli endpoint proxy relativi all'autenticazione.
Inoltra le richieste di login, registrazione e recupero dati utente al backend.
"""
from fastapi import APIRouter, Request, Form, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import date
from typing import Dict, Any, Optional

from utils.models import APIParams
from utils.api_client import call_api

# Creazione del router per il proxy di autenticazione
router = APIRouter(
    tags=["Frontend - Proxy Autenticazione"]
)

templates = Jinja2Templates(directory="templates")

# La funzione accetta un payload JSON (un dizionario) invece di campi di un form.
# Questo la rende coerente con ciò che invia lo script del nuovo login.html.
@router.post("/pagina-login", response_class=JSONResponse)
async def post_login_page(payload: Dict[str, str]) -> JSONResponse:
    '''
    Endpoint per gestire i dati JSON inviati dal form di login.
    Comunica con l'API per autenticare l'utente.
    Args:
        payload (Dict[str, str]): Un dizionario contenente email e password.
    Returns:
        JSONResponse: Risposta JSON con i dati dell'utente autenticato o un errore
    '''
    try:
        # Preparazione dei parametri per la chiamata API usando il payload ricevuto
        login_params: APIParams = APIParams(
            method="POST",
            endpoint="/login",
            payload={"email": payload.get("email"), "password": payload.get("password")}
        )

        # Chiama il backend e restituisce direttamente la sua risposta JSON
        response_data = call_api(login_params)
        return JSONResponse(content=response_data)
        
    except HTTPException as e:
        # Se call_api solleva un'eccezione, la inoltriamo come JSONResponse
        # con il corretto codice di stato e dettaglio.
        return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)

@router.post("/pagina-registrazione-paziente", response_class=HTMLResponse)
async def post_register_page(
    request: Request,
    nome: str = Form(...),
    cognome: str = Form(...),
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

@router.post("/pagina-registrazione-medico", response_class=HTMLResponse)
async def post_medico_register_page(
    request: Request,
    nome: str = Form(...),
    cognome: str = Form(...),
    citta: str = Form(...),
    indirizzo_studio: str = Form(...),
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
            "password": password,
            "indirizzo_studio": indirizzo_studio
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

@router.get("/me")
async def proxy_get_me(authorization: Optional[str] = Header(None)):
    """
    Endpoint proxy che inoltra la richiesta per ottenere i dati dell'utente
    autenticato al backend.
    """
    # Se l'header di autorizzazione non è presente, non possiamo fare nulla.
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
        
    # Estraiamo il token dall'header
    try:
        token_type, token = authorization.split()
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization Header format")

    # Usiamo la funzione call_api per inoltrare la chiamata al backend,
    # passando il token per l'autenticazione.
    api_params = APIParams(method="GET", endpoint="/me")
    
    return call_api(params=api_params, token=token)