import requests
import os
from fastapi import FastAPI, HTTPException, status
from typing import List

# Import dalla cartella utils
from utils.database import get_db_connection, close_db_resources
from utils.models import (
    PazienteRegisration, MedicoRegistration, UserLogin, UserOut,
    SpecializzazioneOut, Token, Messaggio, RichiestaChat, RichiestaOllama, RispostaOllama
)
from utils.auth import pwd_context, create_access_token
from utils.chat_setup import storico_chat, reset_chat 

# Import per il database
import mariadb

app = FastAPI(
    title="Assistente Virtuale Sanitario API",
    description="API per la gestione dell'orientamento sanitario, autenticazione e servizi correlati.",
)

OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL")

# Endpoints dell'API
# Nota: "async" permette a una funzione di "sospendersi" in attesa che un'operazione che richiede tempo sia completata,
# e nel frattempo, il programma può eseguire altro codice.

@app.get("/")
async def read_root():
    return {"message": "Benvenuto nell'API dell'Assistente Virtuale Sanitario!"}

@app.post("/chat", response_model=Messaggio)
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


@app.post("/reset")
def reset_chat_history():
    """
    Resetta la cronologia della chat chiamando la funzione dedicata.
    """
    reset_chat()
    return {"status": "success", "message": "Cronologia chat resettata."}

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