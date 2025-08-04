import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt

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

# Funzioni di autenticazione
# La Secret Key è contenuta nel file .env ed è stata generata col comando `openssl rand -hex 32`, quindi è una stringa casuale di 32 byte (256 bit).
# L'algoritmo di hashing è impostato su HS256 e il tempo di scadenza del token è impostato nel file .env.

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