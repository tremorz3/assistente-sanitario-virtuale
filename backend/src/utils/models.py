from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal, Dict

# Modelli per la registrazione Paziente e Medico

class PazienteRegisration(BaseModel):
    """
    Schema Pydantic per i dati di registrazione di un nuovo paziente.
    """
    email: EmailStr = Field(..., example="mario.rossi@example.com", description="Indirizzo email del paziente (username).")
    password: str = Field(..., min_length=8, example="password123", description="Password scelta dal paziente (minimo 8 caratteri).")
    nome: str = Field(..., min_length=1, max_length=100, example="Mario", description="Nome del paziente.")
    cognome: str = Field(..., min_length=1, max_length=100, example="Rossi", description="Cognome del paziente.")
    telefono: str = Field(..., min_length=10, max_length=10, example="1234567890", description="Numero di telefono del paziente.")

class MedicoRegistration(BaseModel):
    """
    Schema Pydantic per i dati di registrazione di un nuovo medico.
    """
    email: EmailStr = Field(..., example="mario.rossi@example.com", description="Indirizzo email del medico (username).")
    password: str = Field(..., min_length=8, example="password123", description="Password scelta dal medico (minimo 8 caratteri).")
    nome: str = Field(..., min_length=1, max_length=100, example="Mario", description="Nome del medico.")
    cognome: str = Field(..., min_length=1, max_length=100, example="Rossi", description="Cognome del medico.")
    citta: str = Field(..., min_length=1, max_length=100, example="Roma", description="Città di residenza/lavoro del medico.")
    telefono: str = Field(..., min_length=10, max_length=10, example="1234567890", description="Numero di telefono del medico.")
    ordine_iscrizione: str = Field(..., min_length=1, max_length=255, example="Ordine dei Medici di Roma", description="Ordine professionale a cui il medico è iscritto (es. Ordine dei Medici di Roma).")
    numero_iscrizione: str = Field(..., min_length=1, max_length=50, example="12345", description="Numero di iscrizione all'ordine professionale del medico.")
    provincia_iscrizione: str = Field(..., min_length=1, max_length=50, example="Roma", description="Provincia di iscrizione all'ordine professionale del medico.")
    specializzazione_id: int = Field(..., example=10,description="ID della specializzazione principale del medico (riferimento a Specializzazioni).")

# Modelli per autenticazione e risposte Utente
class Token(BaseModel):
    """
    Schema per il token JWT da includere nelle risposte di login.
    """
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    """
    Schema Pydantic per i dati di accesso (login) di un utente.
    """
    email: EmailStr = Field(..., example="utente@example.com", description="Email dell'utente.")
    password: str = Field(..., description="Password dell'utente.")

class UserOut(BaseModel):
    """
    Schema Pydantic per i dati utente da restituire dopo registrazione/login.
    NON include la password_hash per sicurezza.
    """
    id: int = Field(..., description="ID unico dell'utente.")
    email: EmailStr = Field(..., description="Email dell'utente.")
    tipo_utente: str = Field(..., description="Tipo di utente ('medico' o 'paziente').")
    token: Optional[Token] = Field(None, description="Token di accesso JWT. (Opzionale)")

# Modelli per le risorse dell'API
class SpecializzazioneOut(BaseModel):
    """
    Schema Pydantic per la rappresentazione di una specializzazione.
    Utilizzato per la risposta degli endpoint.
    """
    id: int
    nome: str

# Modelli per la funzionalità di chat col modello AI
class Messaggio(BaseModel):
    """
    Rappresenta un singolo messaggio nella cronologia della chat.
    """
    role: Literal["system", "user", "assistant"]
    content: str

class RichiestaChat(BaseModel):
    """
    Schema per la richiesta in arrivo all'endpoint /chat.
    """
    domanda: str
    location: Optional[Dict[str, float]] = None
    client_ip: Optional[str] = None

class RichiestaOllama(BaseModel):
    """
    Schema per il payload da inviare al servizio Ollama.
    """
    model: str = "alibayram/medgemma:4b"
    messages: List[Messaggio]
    stream: bool = False

class RispostaOllama(BaseModel):
    """
    Schema per validare la risposta ricevuta dal servizio Ollama.
    """
    message: Messaggio

