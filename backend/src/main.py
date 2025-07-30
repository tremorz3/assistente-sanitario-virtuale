from fastapi import FastAPI, HTTPException, status 
from pydantic import BaseModel, Field, EmailStr 
from typing import Optional, List
from datetime import datetime

# Libreria per la gestione delle password
from passlib.context import CryptContext

# Import per il database
import mariadb
from .database import get_db_connection, close_db_resources

app = FastAPI(
    title="Assistente Virtuale Sanitario API",
    description="API per la gestione dell'orientamento sanitario, autenticazione e servizi correlati.",
)

# Configurazione per l'hashing delle password
'''
Viene utilizzato l'algoritmo bcrypt per l'hashing delle password, al posto di SHA256, per una questione di sicurezza, in quanto bcrypt è più lento 
nell'hashing, mitigando attacchi tramite rainbow tables.
'''
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Definizione dei modelli Pydantic dei dati

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
    id: int = Field(..., description="ID unico della specializzazione.")
    nome: str = Field(..., max_length=100, description="Nome della specializzazione (es. Cardiologia).")

class UserOut(BaseModel):
    """
    Schema Pydantic per i dati utente da restituire dopo registrazione/login.
    NON include la password_hash per sicurezza.
    """
    id: int = Field(..., description="ID unico dell'utente.")
    email: EmailStr = Field(..., description="Email dell'utente.")
    tipo_utente: str = Field(..., description="Tipo di utente ('medico' o 'paziente').")


"""
Nota: "async" permette a una funzione di "sospendersi" in attesa che un'operazione che richiede tempo sia completata, 
e nel frattempo, il programma può eseguire altro codice.
"""

@app.get("/")
async def read_root():
    return {"message": "Benvenuto nell'Assistente Virtuale Sanitario!"}

@app.post("/register/paziente", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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

@app.post("/register/medico", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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