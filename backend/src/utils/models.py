from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal

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
    indirizzo_studio: str = Field(..., min_length=5, max_length=255, example="Via San Giovanni 1, 04019, Terracina (LT)", description="Indirizzo dello studio medico.")

# Modelli per autenticazione e risposte Utente
class Token(BaseModel):
    """
    Schema per il token JWT da includere nelle risposte di login.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Schema Pydantic per i dati contenuti all'interno di un token JWT.
    """
    email: Optional[str] = None
    id: Optional[int] = None
    tipo_utente: Optional[str] = None

class UserLogin(BaseModel):
    """
    Schema Pydantic per i dati di accesso (login) di un utente.
    """
    email: EmailStr = Field(..., example="utente@example.com", description="Email dell'utente.")
    password: str = Field(..., description="Password dell'utente.")

class UserOut(BaseModel):
    """
    Schema Pydantic per i dati utente da restituire.
    Include l'ID utente generico e l'ID del profilo specifico.
    """
    id: int = Field(..., description="ID unico dell'utente (dalla tabella Utenti).")
    email: EmailStr = Field(..., description="Email dell'utente.")
    tipo_utente: str = Field(..., description="Tipo di utente ('medico' o 'paziente').")
    nome: str = Field(..., description="Nome dell'utente (dal profilo Paziente o Medico).")
    medico_id: Optional[int] = Field(None, description="ID del profilo Medico, se applicabile.")
    paziente_id: Optional[int] = Field(None, description="ID del profilo Paziente, se applicabile.")
    token: Optional[Token] = Field(None, description="Token di accesso JWT. (Opzionale)")

class MedicoOut(BaseModel):
    """
    Schema Pydantic per restituire pubblicamente i dati di un medico.
    Include il nome della specializzazione e omette dati sensibili.
    """
    id: int
    nome: str
    cognome: str
    citta: str
    indirizzo_studio: str
    punteggio_medio: float
    latitudine: Optional[float] = None
    longitudine: Optional[float] = None
    specializzazione_nome: str

    class Config:
        from_attributes = True

class MedicoGeolocalizzatoOut(MedicoOut):
    """
    Schema Pydantic per restituire i dati di un medico geolocalizzato.
    Estende MedicoOut aggiungendo il campo della distanza calcolata e le coordinate.
    """
    distanza_km: float = Field(..., description="Distanza calcolata in chilometri dalla posizione dell'utente.")
    latitudine: float = Field(..., description="Latitudine dello studio medico.")
    longitudine: float = Field(..., description="Longitudine dello studio medico.")

# Modelli per le risorse dell'API
class SpecializzazioneOut(BaseModel):
    """
    Schema Pydantic per la rappresentazione di una specializzazione.
    Utilizzato per la risposta degli endpoint.
    """
    id: int
    nome: str

class AddressSuggestion(BaseModel):
    """
    Rappresenta un singolo suggerimento di indirizzo per l'autocomplete.
    """
    display_address: str
    validation_address: str
    lat: float
    lon: float

# Modelli per la tabella Disponibilità
class DisponibilitaBase(BaseModel):
    """
    Schema base per una fascia oraria di disponibilità.
    """
    data_ora_inizio: datetime = Field(..., description="Inizio della fascia oraria disponibile.")
    data_ora_fine: datetime = Field(..., description="Fine della fascia oraria disponibile.")

class DisponibilitaCreate(DisponibilitaBase):
    """
    Schema utilizzato per creare una nuova disponibilità via API.
    """
    pass

class DisponibilitaOut(DisponibilitaBase):
    """
    Schema per restituire una disponibilità via API, include l'ID e lo stato.
    """
    id: int
    is_prenotato: bool

    class Config:
        from_attributes = True

# Modelli per la tabella Prenotazione
class PrenotazioneBase(BaseModel):
    """
    Schema base per una prenotazione.
    """
    disponibilita_id: int = Field(..., description="ID della fascia oraria che si sta prenotando.")
    note_paziente: Optional[str] = Field(None, description="Note opzionali del paziente per la visita.")

class PrenotazioneCreate(PrenotazioneBase):
    """
    Schema utilizzato per creare una nuova prenotazione via API.
    """
    pass

class PrenotazioneOut(PrenotazioneBase):
    """
    Schema per restituire i dati di una prenotazione.
    """
    id: int
    data_prenotazione: datetime
    stato: Literal['Confermata', 'Completata', 'Cancellata']

    class Config:
        from_attributes = True

class PrenotazioneDetailOut(PrenotazioneOut):
    """
    Schema esteso per i dettagli di una prenotazione per il paziente.
    """
    medico_nome: str
    medico_cognome: str
    data_ora_inizio: datetime

class PrenotazioneMedicoDetailOut(PrenotazioneOut):
    """
    Schema esteso per i dettagli di una prenotazione per il medico.
    """
    paziente_nome: str
    paziente_cognome: str
    paziente_telefono: str
    data_ora_inizio: datetime

class PrenotazioneUpdate(BaseModel):
    """
    Schema utilizzato per aggiornare lo stato di una prenotazione.
    """
    stato: Literal['Completata', 'Cancellata']

# Modelli per la tabella Valutazione
class ValutazioneBase(BaseModel):
    """
    Schema base per una valutazione.
    """
    prenotazione_id: int = Field(..., description="ID della prenotazione da valutare.")
    punteggio: int = Field(..., ge=1, le=5, description="Punteggio da 1 a 5.")
    commento: Optional[str] = Field(None, max_length=1000, description="Commento testuale opzionale.")

class ValutazioneCreate(ValutazioneBase):
    """
    Schema per creare una nuova valutazione via API.
    """
    pass

class ValutazioneOut(ValutazioneBase):
    """
    Schema per restituire i dati di a valutazione.
    """
    id: int
    data_valutazione: datetime

    class Config:
        from_attributes = True

# Modelli per la funzionalità chat
class ChatMessage(BaseModel):
    """
    Schema per i messaggi inviati alla chat AI.
    """
    message: str = Field(..., description="Il messaggio dell'utente da inviare al chatbot.")
    session_id: str = Field(..., description="ID della sessione di conversazione.")

class ChatResponse(BaseModel):
    """
    Schema per le risposte del chatbot AI.
    """
    response: str = Field(..., description="La risposta generata dal chatbot.")
    session_id: str = Field(..., description="ID della sessione di conversazione.")
