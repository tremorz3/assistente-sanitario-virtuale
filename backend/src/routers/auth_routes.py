from fastapi import APIRouter, HTTPException, status, Depends

# Import dei modelli e delle utility necessari
from utils.database import get_db_connection, close_db_resources
from utils.models import PazienteRegisration, MedicoRegistration, UserLogin, UserOut, Token
from utils.auth import pwd_context, create_access_token, get_current_user
from utils.geocoding import get_coordinates

import mariadb

router = APIRouter(
    tags=["Autenticazione e Registrazione"]  # Unico tag per raggruppare questi endpoint
)

@router.post("/register/paziente", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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

@router.post("/register/medico", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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
    # Logica di geocodifica per l'indirizzo dello studio del medico
    lat = None
    lon = None
    if medico.indirizzo_studio:
        coordinates = get_coordinates(medico.indirizzo_studio)
        if coordinates:
            lat, lon = coordinates
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'indirizzo dello studio '{medico.indirizzo_studio}' non è stato trovato o non è valido. Riprova con un indirizzo più preciso."
            )


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
                ordine_iscrizione, numero_iscrizione, provincia_iscrizione, 
                indirizzo_studio, latitudine, longitudine
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query_medico, (
            nuovo_utente_id, medico.specializzazione_id, medico.nome, medico.cognome, medico.citta,
            medico.telefono, medico.ordine_iscrizione, medico.numero_iscrizione, medico.provincia_iscrizione,
            medico.indirizzo_studio, lat, lon
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

@router.post("/login", response_model=UserOut)
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

# Nuovo endpoint "/me" per recuperare il profilo dell'utente loggato.
# Il prefisso del router non c'è, quindi l'URL sarà semplicemente "/me".
@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: UserOut = Depends(get_current_user)):
    """
    Endpoint protetto per recuperare i dati dell'utente attualmente autenticato.

    L'utente viene ottenuto tramite la dipendenza `get_current_user`,
    che valida il token JWT inviato nella richiesta.

    Args:
        current_user (UserOut): L'utente autenticato, iniettato da Depends.

    Returns:
        UserOut: I dati del profilo dell'utente loggato.
    """
    # La dipendenza `get_current_user` fa già tutto il lavoro.
    return current_user
