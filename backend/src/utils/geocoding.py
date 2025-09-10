import requests
from typing import Optional, Tuple, List
from .models import AddressSuggestion

# URL dell'API pubblica di Nominatim (OpenStreetMap)
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"

def get_coordinates(address: str) -> Optional[Tuple[float, float]]:
    """
    Converte un indirizzo testuale in coordinate (latitudine, longitudine)
    usando l'API di Nominatim.

    Args:
        address (str): L'indirizzo da geocodificare.

    Returns:
        Optional[Tuple[float, float]]: Una tupla (latitudine, longitudine) se l'indirizzo
                                        viene trovato, altrimenti None.
    """
    params = {
        'q': address,
        'format': 'json',
        'limit': 1
    }
    
    # È buona norma specificare un User-Agent univoco come richiesto dalla policy di Nominatim
    headers = {
        'User-Agent': 'AssistenteSanitarioTesi/1.0'
    }

    try:
        response = requests.get(NOMINATIM_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()  # Solleva un'eccezione per errori HTTP
        
        data = response.json()
        
        if data:
            # Se troviamo un risultato, estraiamo lat e lon
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return (lat, lon)
        else:
            # Se la risposta è vuota, l'indirizzo non è stato trovato
            return None
            
    except (requests.RequestException, IndexError, KeyError, ValueError) as e:
        print(f"Errore durante la geocodifica dell'indirizzo '{address}': {e}")
        return None
    
def get_address_suggestions(query: str) -> List[AddressSuggestion]:
    """
    Ottiene una lista di suggerimenti di indirizzi basati su una query parziale.
    Ogni suggerimento contiene una versione per il display, una per la validazione e le coordinate.
    Args:
        query (str): La query di ricerca per l'autocomplete degli indirizzi.
    Returns:
        List[AddressSuggestion]: Una lista di oggetti AddressSuggestion con i risultati.
    """
    if not query or len(query) < 3:
        return []

    params = {
        'q': query, 'format': 'json', 'limit': 1, 'addressdetails': 1, 'countrycodes': 'it', 'dedupe': 1
    }
    headers = { 'User-Agent': 'AssistenteSanitarioTesi/1.0' }

    try:
        response = requests.get(NOMINATIM_API_URL, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        suggestions_list = []
        for item in data:
            suggestion_obj = AddressSuggestion(
                display_address=item.get('display_name', '').replace(', Italia', ''),
                validation_address=item.get('display_name', ''),
                lat=float(item.get('lat', 0.0)),
                lon=float(item.get('lon', 0.0))
            )
            suggestions_list.append(suggestion_obj)

        return suggestions_list

    except requests.RequestException as e:
        print(f"Errore durante la richiesta di autocomplete: {e}")
        return []