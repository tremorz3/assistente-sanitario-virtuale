"""
Questo modulo raggruppa tutti gli endpoint del frontend che hanno il solo
scopo di servire e rendere le pagine HTML. Mantenere tutte le viste in un
unico posto semplifica la gestione del routing delle pagine.
"""
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.api_utils import public_call

# Creazione del router per le viste
router = APIRouter(
    tags=["Frontend - Viste HTML"]
)

# Configurazione dei template Jinja2
templates = Jinja2Templates(directory=os.getenv("TEMPLATES_DIR", "templates"))

# Home Page
@router.get("/", response_class=HTMLResponse)
async def serve_home_page(request: Request) -> HTMLResponse:
    """Mostra la pagina principale dell'applicazione."""
    return templates.TemplateResponse("index.html", {"request": request})

# Viste di Autenticazione e Registrazione
@router.get("/pagina-login", response_class=HTMLResponse)
async def get_login_page(request: Request, success: bool = False) -> HTMLResponse:
    """
    Mostra la pagina di login. Può visualizzare un messaggio di successo
    dopo una registrazione andata a buon fine.
    """
    context = {"request": request, "success_message": None}
    if success:
        context["success_message"] = "Registrazione avvenuta con successo! Ora puoi effettuare il login."
    return templates.TemplateResponse("login.html", context)

@router.get("/pagina-registrazione-paziente", response_class=HTMLResponse)
async def get_patient_register_page(request: Request) -> HTMLResponse:
    """Mostra la pagina di registrazione per un nuovo paziente."""
    return templates.TemplateResponse("signup-paziente.html", {"request": request})

@router.get("/pagina-registrazione-medico", response_class=HTMLResponse)
async def get_medico_register_page(request: Request):
    '''
    Mostra la pagina di registrazione per il medico, recuperando dinamicamente
    la lista delle specializzazioni dall'API del backend.
    '''
    try:
        lista_specializzazioni = public_call(method="GET", endpoint="/specializzazioni")

        # Invio della lista al template
        context = {"request": request, "specializzazioni": lista_specializzazioni}
        return templates.TemplateResponse("signup-medico.html", context)

    except HTTPException as e:
        error_msg = f"Impossibile caricare le specializzazioni: {e.detail}"
        context = {"request": request, "error": error_msg}

        return templates.TemplateResponse("signup-medico.html", context)

@router.get("/profilo", response_class=HTMLResponse)
async def get_profile_page(request: Request):
    """
    Serve la pagina del profilo utente.
    Per ora è pubblica, ma in futuro richiederà l'autenticazione.
    """
    return templates.TemplateResponse("profilo.html", {"request": request})

# Viste per i Medici
@router.get("/medici", response_class=HTMLResponse)
async def get_lista_medici_page(request: Request) -> HTMLResponse:
    """Mostra la pagina con l'elenco di tutti i medici iscritti."""
    return templates.TemplateResponse("lista-medici.html", {"request": request})

@router.get("/medici/{medico_id}", response_class=HTMLResponse)
async def get_profilo_medico_page(request: Request) -> HTMLResponse:
    """Mostra la pagina di dettaglio del profilo di un singolo medico."""
    # L'ID del medico verrà estratto dal path nel JavaScript della pagina
    return templates.TemplateResponse("profilo-medico.html", {"request": request})


@router.get("/dashboard-medico", response_class=HTMLResponse)
async def get_medico_dashboard_page(request: Request) -> HTMLResponse:
    """Mostra la dashboard personale del medico."""
    return templates.TemplateResponse("dashboard-medico.html", {"request": request})

@router.get("/gestione-disponibilita", response_class=HTMLResponse)
async def get_gestione_disponibilita_page(request: Request) -> HTMLResponse:
    """Mostra la pagina per la gestione delle proprie disponibilità."""
    return templates.TemplateResponse("gestione-disponibilita.html", {"request": request})

@router.get("/le-mie-recensioni", response_class=HTMLResponse)
async def get_medico_recensioni_page(request: Request) -> HTMLResponse:
    """Mostra la pagina con l'elenco delle recensioni ricevute dal medico."""
    return templates.TemplateResponse("recensioni-medico.html", {"request": request})
