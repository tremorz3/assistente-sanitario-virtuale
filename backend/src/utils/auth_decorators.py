"""
Auth decorators e utilities per eliminare duplicazioni nel controllo autorizzazione.
Fornisce decoratori per validazione tipo utente e helper per gestione profili.
"""

from typing import Any, Tuple
from fastapi import HTTPException, status, Depends

from utils.models import UserOut
from utils.auth import get_current_user
from utils.database_manager import db_transaction, get_doctor_profile_id, get_patient_profile_id


# Helpers interni per evitare duplicazioni nei decorator
def _extract_current_user(args: Tuple[Any, ...], kwargs: dict) -> UserOut:
    """
    Ricava l'istanza di UserOut dagli args/kwargs degli endpoint.
    """
    # Cerca nei kwargs
    for value in kwargs.values():
        if isinstance(value, UserOut):
            return value
    # Cerca negli args
    for arg in args:
        if isinstance(arg, UserOut):
            return arg
    # Se non trovato, errore 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Utente non autenticato."
    )


def _ensure_user_type(current_user: UserOut, expected: str) -> None:
    if current_user.tipo_utente != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accesso riservato ai {expected}."
        )



def get_user_profile_id(profile_type: str, current_user: UserOut) -> int:
    """
    Recupera l'ID del profilo (medico o paziente) per l'utente corrente.
    
    Args:
        profile_type (str): Tipo profilo ('medico' o 'paziente')
        current_user (UserOut): Utente autenticato
        
    Returns:
        int: ID del profilo
        
    Raises:
        HTTPException: Se il profilo non esiste o tipo non valido
    """
    if profile_type not in ['medico', 'paziente']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo profilo deve essere 'medico' o 'paziente'."
        )
    
    # Verifica che l'utente sia del tipo corretto
    if current_user.tipo_utente != profile_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"L'utente deve essere di tipo '{profile_type}'."
        )
    
    with db_transaction() as (conn, cursor):
        if profile_type == 'medico':
            return get_doctor_profile_id(cursor, current_user.id)
        else:  # paziente
            return get_patient_profile_id(cursor, current_user.id)


 


# Helper function per dependency injection semplificata
def get_medico_profile_id(current_user: UserOut = Depends(get_current_user)) -> int:
    """
    Dependency che restituisce l'ID del profilo medico per l'utente corrente.
    
    Usage:
        async def endpoint(medico_id: int = Depends(get_medico_profile_id)):
            # medico_id è automaticamente popolato
            pass
    """
    return get_user_profile_id('medico', current_user)


def get_paziente_profile_id(current_user: UserOut = Depends(get_current_user)) -> int:
    """
    Dependency che restituisce l'ID del profilo paziente per l'utente corrente.
    
    Usage:
        async def endpoint(paziente_id: int = Depends(get_paziente_profile_id)):
            # paziente_id è automaticamente popolato
            pass
    """
    return get_user_profile_id('paziente', current_user)


def validate_user_type_dependency(user_type: str):
    """
    Crea una dependency che valida il tipo utente.
    
    Args:
        user_type (str): Tipo utente richiesto
        
    Returns:
        Dependency function
        
    Usage:
        require_medico = validate_user_type_dependency("medico")
        
        async def endpoint(current_user: UserOut = Depends(require_medico)):
            # Garantito che current_user è un medico
            pass
    """
    def dependency(current_user: UserOut = Depends(get_current_user)) -> UserOut:
        if current_user.tipo_utente != user_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accesso riservato ai {user_type}."
            )
        return current_user
    return dependency


# Dependency predefinite per convenience
require_medico = validate_user_type_dependency("medico")
require_paziente = validate_user_type_dependency("paziente")
