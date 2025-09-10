from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from utils.models import DisponibilitaCreate, DisponibilitaOut
from utils.database_manager import db_transaction, db_readonly
from utils.auth_decorators import get_medico_profile_id

router = APIRouter(
    prefix="/disponibilita",  # Prefisso per tutti gli URL di questo router
    tags=["Disponibilità"]     # Tag per la documentazione API
)

# Endpoints per la gestione delle disponibilità dei medici
@router.post("", response_model=DisponibilitaOut, status_code=status.HTTP_201_CREATED)
async def crea_disponibilita(disponibilita: DisponibilitaCreate, medico_id: int = Depends(get_medico_profile_id)):
    """
    (Protetto) Permette a un medico autenticato di aggiungere una nuova fascia oraria.
    L'ID del medico viene preso automaticamente dal token JWT.
    
    Args:
        disponibilita (DisponibilitaCreate): Dati della nuova disponibilità.
        medico_id (int): ID del profilo medico (auto-iniettato)

    Returns:
        DisponibilitaOut: La disponibilità creata con il suo ID.
        
    Raises:
        HTTPException: Se l'orario si sovrappone o errori database
    """
    with db_transaction() as (conn, cursor):
        # Controllo di sovrapposizione con le disponibilità esistenti
        check_overlap_query = """
            SELECT id FROM Disponibilita
            WHERE medico_id = ? AND (
                ? < data_ora_fine AND  
                ? > data_ora_inizio 
            )
            LIMIT 1
        """
        cursor.execute(check_overlap_query, (
            medico_id,
            disponibilita.data_ora_inizio,
            disponibilita.data_ora_fine
        ))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La fascia oraria specificata si sovrappone con una disponibilità esistente."
            )

        # Inserimento nuova disponibilità
        query = """
            INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine)
            VALUES (?, ?, ?)
        """
        cursor.execute(query, (medico_id, disponibilita.data_ora_inizio, disponibilita.data_ora_fine))
        
        nuova_id = cursor.lastrowid
        
        return DisponibilitaOut(
            id=nuova_id,
            data_ora_inizio=disponibilita.data_ora_inizio,
            data_ora_fine=disponibilita.data_ora_fine,
            is_prenotato=False 
        )

# L'endpoint GET rimane pubblico
@router.get("/medici/{medico_id}", response_model=List[DisponibilitaOut])
async def get_disponibilita_medico(medico_id: int, solo_libere: bool = True):
    """
    Recupera le fasce orarie di disponibilità per un dato medico.

    Args:
        medico_id (int): L'ID del medico.
        solo_libere (bool): Se True, restituisce solo le fasce non prenotate. 

    Returns:
        List[DisponibilitaOut]: Una lista di fasce orarie.
    """
    with db_readonly() as cursor:
        # Vengono mostrate solo le disponibilità future
        query = "SELECT * FROM Disponibilita WHERE medico_id = ? AND data_ora_inizio > NOW()"
        params = [medico_id]
        
        if solo_libere:
            query += " AND is_prenotato = FALSE"

        cursor.execute(query, tuple(params))
        disponibilita = cursor.fetchall()
        return [DisponibilitaOut(**d) for d in disponibilita]

# Assunzione: un Medico non può cancellare uno slot di tempo se un Paziente lo ha già prenotato
@router.delete("/{disponibilita_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancella_disponibilita(disponibilita_id: int, medico_id: int = Depends(get_medico_profile_id)):
    """
    Cancella una fascia oraria di disponibilità, solo se non è prenotata e appartiene al medico autenticato. 

    Args:
        disponibilita_id (int): L'ID della disponibilità da cancellare.
        medico_id (int): ID del profilo medico (auto-iniettato)

    Raises:
        HTTPException: 
            - 404: Se la disponibilità non viene trovata.
            - 409: Se la disponibilità è già stata prenotata.
    """
    with db_transaction() as (conn, cursor):
        # Controlla lo stato della disponibilità prima di cancellarla
        cursor.execute("SELECT medico_id, is_prenotato FROM Disponibilita WHERE id = ?", (disponibilita_id,))
        disponibilita = cursor.fetchone()
        
        if not disponibilita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Disponibilità non trovata."
            )
        
        # Verifica ownership: solo il medico proprietario può cancellare
        if disponibilita['medico_id'] != medico_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Non puoi cancellare la disponibilità di un altro medico."
            )
        
        # Impedisce la cancellazione se già prenotata
        if disponibilita['is_prenotato']:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Impossibile cancellare una disponibilità già prenotata."
            )
            
        # Cancellazione
        cursor.execute("DELETE FROM Disponibilita WHERE id = ?", (disponibilita_id,))
        
        # Verifica successo operazione
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Disponibilità non trovata durante il tentativo di cancellazione."
            )

        return None
