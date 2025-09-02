"""
Questo modulo gestisce tutte le operazioni legate all'autenticazione e alla sicurezza.
Include la creazione e verifica dei token JWT, l'hashing delle password e
la dipendenza FastAPI per ottenere l'utente autenticato dalle richieste API.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Header
import mariadb

from utils.models import TokenData, UserOut
from utils.database import get_db_connection, close_db_resources


# Configurazione sicurezza e costanti
# Carica le variabili d'ambiente per la configurazione dei token JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Configurazione per l'hashing delle password
# Viene utilizzato l'algoritmo bcrypt per l'hashing delle password, al posto di SHA256, per una questione di sicurezza, in quanto bcrypt è più lento
# nell'hashing, mitigando attacchi tramite rainbow tables.
# 'deprecated="auto"' permette di utilizzare le versioni più recenti degli algoritmi di hashing, mantenendo la compatibilità con le versioni precedenti.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Definizione dello schema di sicurezza "HTTP Bearer".
# Questa istanza si occuperà di cercare l'header "Authorization: Bearer <token>"
# nelle richieste in arrivo.
http_bearer_scheme = HTTPBearer(
    description="Schema di autenticazione basato su Bearer Token JWT."
)

# Funzioni di autenticazione
# La Secret Key è contenuta nel file .env ed è stata generata col comando `openssl rand -hex 32`, quindi è una stringa casuale di 32 byte (256 bit).
# L'algoritmo di hashing è impostato su HS256 e il tempo di scadenza del token è impostato nel file .env.

# Funzione per creare un token JWT
def create_access_token(data: dict) -> str:
    '''
    Crea un nuovo token di accesso JWT.
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

# Funzione per la verifica del token JWT
def verify_token(token: str) -> TokenData:
    """
    Decodifica e verifica un token JWT.
    Args:
        token (str): Il token da verificare.
    Returns:
        TokenData: Un oggetto Pydantic con i dati estratti dal token se valido.
    Raises:
        HTTPException: Se il token non è valido (scaduto, malformato, etc.).
    """
    # Prepariamo un'eccezione standard per tutti i casi di fallimento.
    # L'header 'WWW-Authenticate' è una convenzione per le risposte 401.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossibile validare le credenziali",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # La funzione jwt.decode fa il lavoro pesante:
        # 1. Verifica che la firma del token corrisponda alla nostra SECRET_KEY.
        # 2. Verifica che il token non sia scaduto.
        payload: dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Estrae i dati dal payload. Nota: .get() non causa errori se il campo non è presente
        user_id: Optional[int] = payload.get("id")
        email: Optional[str] = payload.get("sub") # "sub" (subject) è un nome standard per l'identificativo utente.
        tipo_utente: Optional[str] = payload.get("tipo_utente")

        if user_id is None or email is None:
            # Se mancano informazioni fondamentali, il token non è valido
            raise credentials_exception
        
        # Restituisce i dati validati usando il modello Pydantic
        return TokenData(id=user_id, email=email, tipo_utente=tipo_utente)

    except JWTError:
        # Se la libreria jose lancia un errore (es. firma non valida, token scaduto) solleva l'eccezione personalizzata
        raise credentials_exception

# Dipendenza di sicurezza
# Depends(http_bearer_scheme) Dice: "Prima di eseguire il codice di questa funzione, esegui lo schema http_bearer_scheme". 
# Se il token non c'è, FastAPI fermerà la richiesta con un errore 401.
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer_scheme)) -> UserOut:
    """
    Dipendenza FastAPI per ottenere l'utente corrente autenticato dal token.

    Questa funzione è il cuore del sistema di sicurezza per gli endpoint.
    Viene "iniettata" negli endpoint protetti per garantire l'autenticazione.

    Args:
        credentials (HTTPAuthorizationCredentials): Oggetto fornito da `Depends(http_bearer_scheme)`, contiene lo schema e 
        il token.

    Raises:
        HTTPException (401/404/500): Sollevata se l'autenticazione fallisce o se si verificano errori.

    Returns:
        UserOut: Un oggetto Pydantic con i dati dell'utente recuperato dal database.
    """
    # La dipendenza HTTPBearer restituisce un oggetto con le credenziali.
    # Il token vero e proprio si trova nell'attributo .credentials
    token = credentials.credentials
    token_data: TokenData = verify_token(token)
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Usiamo LEFT JOIN e COALESCE (restituisce il primo valore non nullo che trova) per recuperare il nome, che sia un
        # paziente o un medico, in una sola query.
        query = """
            SELECT
                u.id, u.email, u.tipo_utente,
                COALESCE(p.nome, m.nome) AS nome,
                p.id AS paziente_id,
                m.id AS medico_id
            FROM Utenti u
            LEFT JOIN Pazienti p ON u.id = p.utente_id
            LEFT JOIN Medici m ON u.id = m.utente_id
            WHERE u.id = ?
        """
        cursor.execute(query, (token_data.id,))
        user_data = cursor.fetchone()
        
        if user_data is None or user_data.get('nome') is None:
            # Se l'utente non esiste o non ha un profilo associato, l'autenticazione fallisce.
            raise HTTPException(status_code=404, detail="User not found or profile incomplete")
            
        return UserOut(**user_data)
        
    except mariadb.Error:
        raise HTTPException(status_code=500, detail="Database error during user retrieval")
    finally:
        close_db_resources(conn, cursor)

# Dipendenza opzionale per autenticazione
def get_optional_current_user(authorization: Optional[str] = Header(None)) -> Optional[UserOut]:
    """
    Dipendenza FastAPI per ottenere l'utente corrente se autenticato, altrimenti None.
    
    Questa funzione permette di avere endpoint che funzionano sia per utenti 
    autenticati che non autenticati.
    
    Args:
        authorization (Optional[str]): Header Authorization se presente
        
    Returns:
        Optional[UserOut]: Utente se autenticato, None altrimenti
    """
    if not authorization or not authorization.startswith('Bearer '):
        return None
    
    try:
        token = authorization.split(' ')[1]
        token_data: TokenData = verify_token(token)
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT
                    u.id, u.email, u.tipo_utente,
                    COALESCE(p.nome, m.nome) AS nome,
                    p.id AS paziente_id,
                    m.id AS medico_id
                FROM Utenti u
                LEFT JOIN Pazienti p ON u.id = p.utente_id
                LEFT JOIN Medici m ON u.id = m.utente_id
                WHERE u.id = ?
            """
            cursor.execute(query, (token_data.id,))
            user_data = cursor.fetchone()
            
            if user_data is None or user_data.get('nome') is None:
                return None
                
            return UserOut(**user_data)
            
        except mariadb.Error:
            return None
        finally:
            close_db_resources(conn, cursor)
            
    except (HTTPException, JWTError):
        return None

