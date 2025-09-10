# frontend/src/utils/auth_utils.py
"""
Utility per la gestione dell'autenticazione JWT nel frontend.
Elimina la duplicazione del parsing dell'Authorization header across tutti i proxy.
"""
from fastapi import HTTPException
from typing import Optional


def extract_jwt_token(authorization: Optional[str]) -> Optional[str]:
    """
    Estrae il token JWT dall'header Authorization in modo sicuro.
    
    Args:
        authorization (Optional[str]): Il valore dell'header Authorization (formato: "Bearer <token>")
        
    Returns:
        Optional[str]: Il token JWT estratto, oppure None se authorization è None
        
    Raises:
        HTTPException: Se il formato dell'header è invalido o il tipo di token non è Bearer
    """
    if authorization is None:
        return None
        
    try:
        token_type, token = authorization.split()
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return token
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization Header format")


def require_authorization(authorization: Optional[str]) -> str:
    """
    Wrapper che richiede la presenza del token di autorizzazione.
    
    Args:
        authorization (Optional[str]): Il valore dell'header Authorization
        
    Returns:
        str: Il token JWT estratto
        
    Raises:
        HTTPException: Se l'header è mancante o invalido
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
        
    return extract_jwt_token(authorization)