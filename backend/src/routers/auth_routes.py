from fastapi import APIRouter, HTTPException, status, Depends

# Import dei modelli e delle utility necessari
from utils.models import PazienteRegisration, MedicoRegistration, UserLogin, UserOut, Token
from utils.auth import pwd_context, create_access_token, get_current_user
from utils.geocoding import get_coordinates
from utils.database_manager import (
    db_transaction, 
    db_readonly,
    execute_insert_get_id,
    validate_specialization_exists
)

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
    hashed_password: str = pwd_context.hash(paziente.password)

    with db_transaction(dictionary=False) as (conn, cursor):
        # Query per l'inserimento di un nuovo utente 
        query_utente = "INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'paziente')"
        nuovo_utente_id = execute_insert_get_id(cursor, query_utente, (paziente.email, hashed_password))

        # Query per l'inserimento del paziente
        query_paziente = "INSERT INTO Pazienti (utente_id, nome, cognome, telefono) VALUES (?, ?, ?, ?)"
        execute_insert_get_id(cursor, query_paziente, (nuovo_utente_id, paziente.nome, paziente.cognome, paziente.telefono))

        return UserOut(id=nuovo_utente_id, email=paziente.email, tipo_utente="paziente", nome=paziente.nome)

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


    with db_transaction() as (conn, cursor):
        # Verifica dell'esistenza della specializzazione
        validate_specialization_exists(cursor, medico.specializzazione_id)

        hashed_password: str = pwd_context.hash(medico.password)

        # Inserimento utente
        query_utente = "INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'medico')"
        nuovo_utente_id = execute_insert_get_id(cursor, query_utente, (medico.email, hashed_password))

        # Inserimento medico
        query_medico = """
            INSERT INTO Medici (
                utente_id, specializzazione_id, nome, cognome, citta, telefono, 
                ordine_iscrizione, numero_iscrizione, provincia_iscrizione, 
                indirizzo_studio, latitudine, longitudine
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_insert_get_id(cursor, query_medico, (
            nuovo_utente_id, medico.specializzazione_id, medico.nome, medico.cognome, medico.citta,
            medico.telefono, medico.ordine_iscrizione, medico.numero_iscrizione, medico.provincia_iscrizione,
            medico.indirizzo_studio, lat, lon
        ))

        # Commit automatico da db_transaction
        return UserOut(id=nuovo_utente_id, email=medico.email, tipo_utente="medico", nome=medico.nome)

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
    with db_readonly() as cursor:
        # Query per recuperare l'utente nel database
        query = """
            SELECT
                u.id, u.email, u.password_hash, u.tipo_utente,
                COALESCE(p.nome, m.nome) AS nome
            FROM Utenti u
            LEFT JOIN Pazienti p ON u.id = p.utente_id
            LEFT JOIN Medici m ON u.id = m.utente_id
            WHERE u.email = ?
        """
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

        return UserOut(
            id=utente['id'], 
            email=utente['email'], 
            tipo_utente=utente['tipo_utente'], 
            nome=utente['nome'], 
            token=token
        )

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
