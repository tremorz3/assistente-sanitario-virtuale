import os
from fastapi import FastAPI, HTTPException, status 
from pydantic import BaseModel, Field, EmailStr 
from typing import Optional, List
from datetime import datetime, timedelta, timezone

# Libreria per la gestione delle password
from passlib.context import CryptContext
# Libreria per la gestione dei token JWT
from jose import JWTError, jwt

# Import per il database
import mariadb
from database import get_db_connection, close_db_resources

app = FastAPI(
    title="Assistente Virtuale Sanitario API",
    description="API per la gestione dell'orientamento sanitario, autenticazione e servizi correlati.",
)

# Definizione delle costanti per la gestione dei token JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Configurazione per l'hashing delle password
'''
Viene utilizzato l'algoritmo bcrypt per l'hashing delle password, al posto di SHA256, per una questione di sicurezza, in quanto bcrypt è più lento 
nell'hashing, mitigando attacchi tramite rainbow tables.
'''
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Definizione dei modelli Pydantic dei dati

# Modello per i token di login
class Token(BaseModel):
    access_token: str
    token_type: str

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

class UserLogin(BaseModel):
    """
    Schema Pydantic per i dati di accesso (login) di un utente.
    """
    email: EmailStr = Field(..., example="utente@example.com", description="Email dell'utente.")
    password: str = Field(..., description="Password dell'utente.")

# Modelli di risposta API (Output):

# Modello per la risposta di Specializzazione (utile per recuperare Specializzazioni)
class SpecializzazioneOut(BaseModel):
    """
    Schema Pydantic per la rappresentazione di una specializzazione.
    Utilizzato per la risposta degli endpoint.
    """
    id: int
    nome: str

class UserOut(BaseModel):
    """
    Schema Pydantic per i dati utente da restituire dopo registrazione/login.
    NON include la password_hash per sicurezza.
    """
    id: int = Field(..., description="ID unico dell'utente.")
    email: EmailStr = Field(..., description="Email dell'utente.")
    tipo_utente: str = Field(..., description="Tipo di utente ('medico' o 'paziente').")
    token: Optional[Token] = Field(None, description="Token di accesso JWT. (Opzionale)")

'''
La Secret Key è contenuta nel file .env ed è stata generata col comando `openssl rand -hex 32`, quindi è una stringa casuale di 32 byte (256 bit).
L'algoritmo di hashing è impostato su HS256 e il tempo di scadenza del token è impostato nel file .env.
'''
# Funzione per creare un token JWT
def create_access_token(data: dict) -> str:
    '''
    Args:
        data (dict): Dati da includere nel token JWT, come email, ID utente e tipo utente.
    Returns:
        str: Token JWT codificato.
    '''
    # Copia i dati di login per evitare modifiche indesiderate ai dati dell'utente
    to_encode: dict = data.copy() 

    # Imposta la data di scadenza del token
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Crea il token JWT utilizzando la chiave segreta e l'algoritmo specificato
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

# Endpoints dell'API
"""
Nota: "async" permette a una funzione di "sospendersi" in attesa che un'operazione che richiede tempo sia completata, 
e nel frattempo, il programma può eseguire altro codice.
"""

@app.get("/")
async def read_root():
    return {"message": "Benvenuto nell'API dell'Assistente Virtuale Sanitario!"}

@app.post("/register/paziente", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Registrazione"])
async def register_paziente(paziente: PazienteRegisration) -> UserOut:
    '''
    Registra un nuovo paziente nel database.
    Args:
        paziente (PazienteRegisration): Dati del paziente da registrare.
    Returns:
        UserOut: Dati dell'utente registrato (ID, email, tipo utente).
    Raises:
        HTTPException: Se si verifica un errore durante la registrazione.
    '''
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password: str = pwd_context.hash(paziente.password)

        # Query per l'inserimento di un nuovo utente 
        query_utente: str = "INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'paziente')"
        cursor.execute(query_utente, (paziente.email, hashed_password))
        
        nuovo_utente_id: int = cursor.lastrowid # Recupera l'ID dell'ultimo utente inserito

        # Query per l'inserimento del paziente
        query_paziente: str = "INSERT INTO Pazienti (utente_id, nome, cognome, telefono) VALUES (?, ?, ?, ?)"
        cursor.execute(query_paziente, (nuovo_utente_id, paziente.nome, paziente.cognome, paziente.telefono))

        conn.commit() # Salva le modifiche nel database
        return UserOut(id=nuovo_utente_id, email=paziente.email, tipo_utente="paziente")
    except mariadb.IntegrityError:
        # Errore specifico per violazione di un vincolo (es. email UNIQUE)
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un utente con l'email '{paziente.email}' esiste già."
        )
    except mariadb.Error as e:
        # Qualsiasi altro errore del database
        if conn:
            conn.rollback()
        # Non si espone direttamente l'errore 'e' all'utente per sicurezza
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno durante la registrazione."
        )
    finally:
        close_db_resources(conn, cursor)

@app.post("/register/medico", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Registrazione"])
async def register_medico(medico: MedicoRegistration) -> UserOut:
    '''
    Registra un nuovo medico nel database.
    Args:
        medico (MedicoRegistration): Dati del medico da registrare.
    Returns:
        UserOut: Dati dell'utente registrato (ID, email, tipo utente).
    Raises:
        HTTPException: Se si verifica un errore durante la registrazione.
    '''
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        # dictionary=True fa sì che le query SELECT restituiscano i risultati come dizionari, invece di tuple
        cursor = conn.cursor(dictionary=True) 

        # Verifica dell'esistenza della specializzazione
        cursor.execute("SELECT id FROM Specializzazioni WHERE id = ?", (medico.specializzazione_id,))
        if cursor.fetchone() is None:
            # Se la query non trova l'ID, la specializzazione non è valida
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La specializzazione con ID {medico.specializzazione_id} non esiste."
            )
        
        hashed_password: str = pwd_context.hash(medico.password)

        # Query per l'inserimento di un nuovo utente
        query_utente = "INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'medico')"
        cursor.execute(query_utente, (medico.email, hashed_password))

        nuovo_utente_id: int = cursor.lastrowid  # Recupera l'ID dell'ultimo utente inserito

        # Query per l'inserimento del medico
        query_medico = """
            INSERT INTO Medici (
                utente_id, specializzazione_id, nome, cognome, citta, telefono, 
                ordine_iscrizione, numero_iscrizione, provincia_iscrizione
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_medico, (
            nuovo_utente_id, medico.specializzazione_id, medico.nome, medico.cognome, medico.citta,
            medico.telefono, medico.ordine_iscrizione, medico.numero_iscrizione, medico.provincia_iscrizione
        ))

        conn.commit()
        return UserOut(id=nuovo_utente_id, email=medico.email, tipo_utente="medico")
    except mariadb.IntegrityError:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un utente con l'email '{medico.email}' esiste già."
        )
    except mariadb.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno durante la registrazione."
        )
    finally:
        close_db_resources(conn, cursor)

@app.post("/login", response_model=UserOut, tags=["Autenticazione"])
async def login(user: UserLogin) ->  UserOut:
    '''
    Autentica un utente e restituisce un token di accesso. 
    Args:
        user (UserLogin): Dati di accesso dell'utente (email e password).
    Returns:
        UserOut: Dati dell'utente autenticato (ID, email, tipo utente, token di accesso).
    Raises:
        HTTPException: Se le credenziali non sono valide o si verifica un errore durante il login.  
    '''
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query per recuperare l'utente nel database
        query: str = "SELECT id, email, password_hash, tipo_utente FROM Utenti WHERE email = ?"
        cursor.execute(query, (user.email,))
        utente = cursor.fetchone()

        # Se l'utente non esiste o la password è sbagliata, lancia un'eccezione
        if not utente or not pwd_context.verify(user.password, utente['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o password non validi.",            
            )
        
        # Se le credenziali sono corrette, crea il token di accesso
        access_token: str = create_access_token(data={"sub": utente['email'], "id": utente['id'], "tipo_utente": utente['tipo_utente']})
        token: Token = Token(access_token=access_token, token_type="bearer")

        # Bearer Token è uno standard per l'autenticazione, che specifica che il portatore (bearer) del token ha accesso alle risorse protette
        return UserOut(id=utente['id'], email=utente['email'], tipo_utente=utente['tipo_utente'], token=token)
    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno durante il login."
        )
    finally:
        close_db_resources(conn, cursor)
        
@app.get("/specializzazioni", response_model=List[SpecializzazioneOut], tags=["Specializzazioni"])
async def get_specializzazioni() -> List[SpecializzazioneOut]:
    '''
    Recupera tutte le specializzazioni dal database.
    Returns:
        List[SpecializzazioneOut]: Lista di oggetti SpecializzazioneOut.
    Raises:
        HTTPException: Se si verifica un errore durante il recupero delle specializzazioni.
    '''
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Specializzazioni")
        specializzazioni = cursor.fetchall()
        return [SpecializzazioneOut(**spec) for spec in specializzazioni]
    except mariadb.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Si è verificato un errore interno durante il recupero delle specializzazioni."
        )
    finally:
        close_db_resources(conn, cursor)