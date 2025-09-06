# frontend/src/utils/api_utils.py
"""
Utility per semplificare le chiamate API nel frontend.
Elimina la duplicazione nella costruzione di APIParams e nelle chiamate autenticate.
"""
from typing import Optional, Dict, Any
from utils.models import APIParams
from utils.api_client import call_api
from utils.auth_utils import extract_jwt_token


def create_api_params(method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> APIParams:
    """
    Factory function per creare oggetti APIParams in modo consistente.
    
    Args:
        method (str): HTTP method (GET, POST, PATCH, DELETE, etc.)
        endpoint (str): Backend endpoint path
        payload (Optional[Dict[str, Any]]): Request payload per POST/PATCH
        
    Returns:
        APIParams: Oggetto parametri configurato per call_api
    """
    return APIParams(method=method, endpoint=endpoint, payload=payload)


def authenticated_call(method: str, endpoint: str, authorization: Optional[str], payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Helper per chiamate API autenticate. Gestisce automaticamente l'estrazione del token.
    
    Args:
        method (str): HTTP method 
        endpoint (str): Backend endpoint path
        authorization (Optional[str]): Authorization header value
        payload (Optional[Dict[str, Any]]): Request payload
        
    Returns:
        Dict[str, Any]: Response dal backend
    """
    token = extract_jwt_token(authorization)
    api_params = create_api_params(method, endpoint, payload)
    return call_api(params=api_params, token=token)


def public_call(method: str, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Helper per chiamate API pubbliche (senza autenticazione).
    
    Args:
        method (str): HTTP method
        endpoint (str): Backend endpoint path  
        payload (Optional[Dict[str, Any]]): Request payload
        
    Returns:
        Dict[str, Any]: Response dal backend
    """
    api_params = create_api_params(method, endpoint, payload)
    return call_api(params=api_params)