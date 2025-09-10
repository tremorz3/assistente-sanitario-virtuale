from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

# Import dei modelli e delle utility necessarie
from utils.models import (
    PrenotazioneCreate, 
    PrenotazioneOut, 
    PrenotazioneUpdate, 
    PrenotazioneDetailOut, 
    PrenotazioneMedicoDetailOut, 
    UserOut
)
from utils.database_manager import db_transaction, db_readonly
from utils.auth import get_current_user
from utils.auth_decorators import get_paziente_profile_id, get_medico_profile_id, require_medico, require_paziente

router = APIRouter(
    prefix="/prenotazioni",  # Tutti gli URL di questo file inizieranno con /prenotazioni
    tags=["Prenotazioni"]
)

@router.post("", response_model=PrenotazioneOut, status_code=status.HTTP_201_CREATED)
async def crea_prenotazione(prenotazione: PrenotazioneCreate, paziente_id: int = Depends(get_paziente_profile_id)):
    """
    Crea una nuova prenotazione per una fascia oraria disponibile e per un paziente autenticato.
    
    Questa operazione è svolta in una transazione per garantire l'integrità dei dati nel db:
    1. Verifica che la disponibilità esista e sia libera.
    2. Aggiorna la disponibilità come "prenotata".
    3. Crea la nuova prenotazione.
    
    Se uno qualsiasi di questi passaggi fallisce, l'intera operazione viene annullata.

    Args:
        prenotazione (PrenotazioneCreate): Dati per la nuova prenotazione, contenente disponibilita_id e paziente_id.

    Returns:
        PrenotazioneOut: L'oggetto della prenotazione creata.
        
    Raises:
        HTTPException: 
            - 404: Se la disponibilità o il paziente non esistono.
            - 409: Se la disponibilità è già stata prenotata.
            - 500: Per errori interni del database.
    """
    with db_transaction() as (conn, cursor):

        # 1. Controlla e blocca la riga di disponibilità per l'aggiornamento.
        # 'FOR UPDATE' è fondamentale per prevenire che due utenti prenotino
        # lo stesso slot contemporaneamente (race condition).
        # Questa istruzione dice al database: "Voglio leggere questa riga, ma la sto per modificare, quindi nessun altro processo deve 
        # toccarla finché non ho finito". 
        cursor.execute("SELECT * FROM Disponibilita WHERE id = ? FOR UPDATE", (prenotazione.disponibilita_id,))
        disponibilita = cursor.fetchone()

        if not disponibilita:
            raise HTTPException(status_code=404, detail="Fascia oraria di disponibilità non trovata.")

        if disponibilita['is_prenotato']:
            raise HTTPException(status_code=409, detail="Questa fascia oraria è già stata prenotata.")

        # 2. Aggiorna la disponibilità per marcarla come prenotata
        cursor.execute("UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = ?", (prenotazione.disponibilita_id,))

        # 3. Crea la nuova prenotazione
        query_insert = """
            INSERT INTO Prenotazioni (disponibilita_id, paziente_id, note_paziente)
            VALUES (?, ?, ?)
        """
        cursor.execute(query_insert, (prenotazione.disponibilita_id, paziente_id, prenotazione.note_paziente))
        
        nuova_prenotazione_id = cursor.lastrowid

        # Se tutti i passaggi hanno successo, rende le modifiche permanenti.
        # Commit avviene automaticamente nel context manager

        # Recupera i dati della prenotazione appena creata per restituirli
        cursor.execute("SELECT * FROM Prenotazioni WHERE id = ?", (nuova_prenotazione_id,))
        nuova_prenotazione_data = cursor.fetchone()

        return PrenotazioneOut(**nuova_prenotazione_data)

@router.get("/paziente/me", response_model=List[PrenotazioneDetailOut])
async def get_my_prenotazioni_paziente(paziente_id: int = Depends(get_paziente_profile_id)) -> List[PrenotazioneDetailOut]:
    """
    Recupera tutte le prenotazioni del paziente autenticato con dettagli medico.
    
    Args:
        paziente_id (int): ID del profilo paziente (auto-iniettato)

    Returns:
        List[PrenotazioneDetailOut]: Lista prenotazioni con dettagli
    """
    with db_readonly() as cursor:
        # Query con JOIN per dettagli completi
        query = """
            SELECT 
                p.*,
                m.nome AS medico_nome,
                m.cognome AS medico_cognome,
                d.data_ora_inizio
            FROM Prenotazioni p
            JOIN Disponibilita d ON p.disponibilita_id = d.id
            JOIN Medici m ON d.medico_id = m.id
            WHERE p.paziente_id = ? 
            ORDER BY d.data_ora_inizio DESC
        """
        cursor.execute(query, (paziente_id,))
        prenotazioni = cursor.fetchall()
        return [PrenotazioneDetailOut(**p) for p in prenotazioni]

@router.get("/medico/me", response_model=List[PrenotazioneMedicoDetailOut])
async def get_my_prenotazioni_medico(medico_id: int = Depends(get_medico_profile_id)) -> List[PrenotazioneMedicoDetailOut]:
    """
    Recupera la lista di tutte le prenotazioni associate a al medico loggato, arricchite di dettagli del paziente.
    Questo richiede un JOIN attraverso la tabella Disponibilita.

    Args:
        medico_id (int): L'ID del medico.

    Returns:
        List[PrenotazioneOut]: Una lista di oggetti prenotazione.
    """
    with db_readonly() as cursor:
        # Query che unisce Prenotazioni e Disponibilita
        # per trovare gli appuntamenti di un medico.
        query = """
            SELECT 
                p.*,
                paz.nome AS paziente_nome,
                paz.cognome AS paziente_cognome,
                paz.telefono AS paziente_telefono,
                d.data_ora_inizio
            FROM Prenotazioni p
            JOIN Disponibilita d ON p.disponibilita_id = d.id
            JOIN Pazienti paz ON p.paziente_id = paz.id
            WHERE d.medico_id = ?
            ORDER BY d.data_ora_inizio ASC
        """
        cursor.execute(query, (medico_id,))
        prenotazioni = cursor.fetchall()
        return [PrenotazioneMedicoDetailOut(**p) for p in prenotazioni]

# Introduce una logica di autorizzazione più complessa, dove diversi ruoli (medico e paziente) possono compiere la 
# stessa azione, ma con permessi differenti.
@router.patch("/{prenotazione_id}", response_model=PrenotazioneOut)
async def aggiorna_stato_prenotazione(
    prenotazione_id: int, 
    update_data: PrenotazioneUpdate,
    current_user: UserOut = Depends(get_current_user)
):
    """
    Aggiorna lo stato di una prenotazione esistente.
    Permette di marcare una prenotazione come 'Completata' o 'Cancellata'.
    Regole di autorizzazione:
    - Stato 'Completata': Può essere impostato solo dal medico associato alla visita.
    - Stato 'Cancellata': Può essere impostato dal paziente che ha prenotato o dal medico.

    Args:
        prenotazione_id (int): L'ID della prenotazione da aggiornare.
        update_data (PrenotazioneUpdate): I dati per l'aggiornamento (il nuovo stato).

    Returns:
        PrenotazioneOut: L'oggetto della prenotazione con lo stato aggiornato.

    Raises:
        HTTPException:
            - 404: Se la prenotazione non viene trovata.
            - 409: Se si tenta di cancellare una prenotazione già completata (o viceversa).
            - 500: Per errori interni del database.
    """
    with db_transaction() as (conn, cursor):

        # Recupera i dati della prenotazione e le informazioni collegate per i controlli
        query_prenotazione = """
            SELECT 
                p.id, p.stato, p.paziente_id,
                d.medico_id
            FROM Prenotazioni p
            JOIN Disponibilita d ON p.disponibilita_id = d.id
            WHERE p.id = ?
            FOR UPDATE
        """
        cursor.execute(query_prenotazione, (prenotazione_id,))
        prenotazione = cursor.fetchone()

        if not prenotazione:
            raise HTTPException(status_code=404, detail="Prenotazione non trovata.")

        # Regola di business: non si può modificare una prenotazione già cancellata o completata.
        if prenotazione['stato'] in ['Completata', 'Cancellata']:
            raise HTTPException(
                status_code=409,
                detail=f"La prenotazione è già nello stato finale '{prenotazione['stato']}' e non può essere modificata."
            )
        
        # Gestione autorizzazioni basata sul tipo di aggiornamento
        # CASO 1: Aggiornamento a 'Completata' - solo il medico della visita può farlo
        if update_data.stato == 'Completata':
            if current_user.tipo_utente != 'medico':
                raise HTTPException(status_code=403, detail="Azione non permessa. Solo i medici possono completare le visite.")
            
            # Verifica che sia il medico giusto per questa prenotazione
            from utils.auth_decorators import get_user_profile_id
            medico_profile_id = get_user_profile_id('medico', current_user)
            if prenotazione['medico_id'] != medico_profile_id:
                raise HTTPException(status_code=403, detail="Azione non permessa. Solo il medico della visita può completarla.")
        
        # CASO 2: Aggiornamento a 'Cancellata' - paziente o medico possono farlo
        elif update_data.stato == 'Cancellata':
            from utils.auth_decorators import get_user_profile_id
            
            if current_user.tipo_utente == 'paziente':
                paziente_profile_id = get_user_profile_id('paziente', current_user)
                is_paziente_proprietario = prenotazione['paziente_id'] == paziente_profile_id
            else:
                is_paziente_proprietario = False
            
            if current_user.tipo_utente == 'medico':
                medico_profile_id = get_user_profile_id('medico', current_user)
                is_medico_proprietario = prenotazione['medico_id'] == medico_profile_id
            else:
                is_medico_proprietario = False
            
            if not (is_paziente_proprietario or is_medico_proprietario):
                raise HTTPException(status_code=403, detail="Azione non permessa. Non puoi cancellare questa prenotazione.")
            
            # Se la prenotazione viene cancellata, liberiamo lo slot
            cursor.execute(
                "UPDATE Disponibilita SET is_prenotato = FALSE WHERE id = (SELECT disponibilita_id FROM Prenotazioni WHERE id = ?)",
                (prenotazione_id,)
            )

        # Aggiorna lo stato della prenotazione
        query_update = "UPDATE Prenotazioni SET stato = ? WHERE id = ?"
        cursor.execute(query_update, (update_data.stato, prenotazione_id))
        # Commit automatico nel context manager

        # Recupera e restituisce la prenotazione aggiornata
        cursor.execute("SELECT * FROM Prenotazioni WHERE id = ?", (prenotazione_id,))
        prenotazione_aggiornata = cursor.fetchone()
        return PrenotazioneOut(**prenotazione_aggiornata)
