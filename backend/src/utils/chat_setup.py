from typing import List
from .models import Messaggio 

def leggi_prompt_da_file(percorso_file: str) -> str:
    """
    Legge e restituisce il contenuto di un file di testo.
    Args:
        percorso_file (str): Il percorso del file da leggere.
    Returns:
        str: Il contenuto del file, senza spazi iniziali o finali."""
    with open(percorso_file, 'r', encoding='utf-8') as f:
        return f.read().strip()
    
# Carica il prompt di sistema dal file co-locato
PROMPT_DI_SISTEMA: str = leggi_prompt_da_file("./utils/prompt.txt")

# Inizializza la cronologia della chat come variabile globale di questo modulo
storico_chat: List[Messaggio] = [
    Messaggio(role="system", content=PROMPT_DI_SISTEMA)
]

def reset_chat():
    """
    Resetta la cronologia della chat, mantenendo solo il prompt di sistema iniziale.
    """
    global storico_chat
    storico_chat.clear()
    storico_chat.append(Messaggio(role="system", content=PROMPT_DI_SISTEMA))