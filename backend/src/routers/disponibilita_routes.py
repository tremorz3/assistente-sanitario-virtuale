from fastapi import APIRouter, HTTPException, status
from typing import List
import mariadb

from utils.models import DisponibilitaCreate, DisponibilitaOut
from utils.database import get_db_connection, close_db_resources

router = APIRouter(
    prefix="/disponibilita",  # Prefisso per tutti gli URL di questo router
    tags=["Disponibilità"]     # Tag per la documentazione API
)

# Endpoints per la gestione delle disponibilità dei medici
@router.post("/medici/{medico_id}", response_model=DisponibilitaOut, status_code=status.HTTP_201_CREATED)
async def crea_disponibilita(medico_id: int, disponibilita: DisponibilitaCreate):
    """
    Permette a un medico di aggiungere una nuova fascia oraria di disponibilità. Nota: le fasce orarie devono essere contigue e non sovrapporsi 
    ad altre prenotazioni. La logica per verificare se due intervalli di tempo si sovrappongono è la seguente: un nuovo intervallo 
    (nuovo_inizio, nuova_fine) si sovrappone a un intervallo esistente (db_inizio, db_fine) se e solo se l'inizio del nuovo intervallo 
    è precedente alla fine di quello esistente e la fine del nuovo intervallo è successiva all'inizio di quello esistente.

    Args:
        medico_id (int): L'ID del medico che aggiunge la disponibilità.
        disponibilita (DisponibilitaCreate): Dati della nuova disponibilità.

    Returns:
        DisponibilitaOut: La disponibilità creata con il suo ID.
        
    Raises:
        HTTPException: Se il medico non esiste, se l'orario si sovrappone o se si verifica un errore nel database
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Controlla se il medico esiste
        cursor.execute("SELECT id FROM Medici WHERE id = ?", (medico_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medico non trovato.")


        # Controllo di sovrapposizione con le disponibilità esistenti
        # Query per trovare eventuali slot che si sovrappongono al nuovo intervallo.
        # Il tipo di dato DATETIME nel database contiene sia la data che l'ora in un unico valore. 
        # Quando si confrontano due campi DATETIME, il database confronta l'intero valore, partendo dall'anno fino ai secondi.
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

        query = """
            INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine)
            VALUES (?, ?, ?)
        """
        cursor.execute(query, (medico_id, disponibilita.data_ora_inizio, disponibilita.data_ora_fine))
        
        nuova_id = cursor.lastrowid
        conn.commit()
        
        return DisponibilitaOut(
            id=nuova_id,
            medico_id=medico_id,
            data_ora_inizio=disponibilita.data_ora_inizio,
            data_ora_fine=disponibilita.data_ora_fine,
            is_prenotato=False 
        )

    except mariadb.Error as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore interno durante la creazione della disponibilità: {e}"
        )
    finally:
        close_db_resources(conn, cursor)

@router.get("/medici/{medico_id}", response_model=List[DisponibilitaOut])
async def get_disponibilita_medico(medico_id: int, solo_libere: bool = True):
    """
    Recupera le fasce orarie di disponibilità per un dato medico.

    Args:
        medico_id (int): L'ID del medico.
        solo_libere (bool): Se True, restituisce solo le fasce non ancora prenotate,se False, restituisce tutte le fasce orarie. 

    Returns:
        List[DisponibilitaOut]: Una lista di fasce orarie.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM Disponibilita WHERE medico_id = ?"
        params = [medico_id]
        
        if solo_libere:
            query += " AND is_prenotato = FALSE"

        cursor.execute(query, tuple(params))
        
        disponibilita = cursor.fetchall()
        return [DisponibilitaOut(**d) for d in disponibilita]

    except mariadb.Error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore nel recupero delle disponibilità."
        )
    finally:
        close_db_resources(conn, cursor)

# Assunzione: un Medico non può cancellare uno slot di tempo se un Paziente lo ha già prenotato
@router.delete("{disponibilita_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancella_disponibilita(disponibilita_id: int):
    """
    Cancella una fascia oraria di disponibilità, solo se non è prenotata.

    Args:
        disponibilita_id (int): L'ID della disponibilità da cancellare.

    Raises:
        HTTPException: 
            - 404: Se la disponibilità non viene trovata.
            - 409: Se la disponibilità è già stata prenotata e non può essere cancellata.
            - 500: Per errori interni del database.
    """
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Controlla lo stato della disponibilità prima di cancellarla
        cursor.execute("SELECT is_prenotato FROM Disponibilita WHERE id = ?", (disponibilita_id,))
        disponibilita = cursor.fetchone()
        
        if not disponibilita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Disponibilità non trovata."
            )
        
        # Impedisce la cancellazione se già prenotata
        if disponibilita['is_prenotato']:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Impossibile cancellare una disponibilità già prenotata."
            )
            
        # Se non è prenotata la cancella
        cursor.execute("DELETE FROM Disponibilita WHERE id = ?", (disponibilita_id,))
        conn.commit()
        
        # Controlla se la riga è stata effettivamente cancellata
        if cursor.rowcount == 0:
            # Questo caso può verificarsi in una "race condition", dove un altro processo
            # cancella la riga tra il SELECT e il DELETE. È una sicurezza aggiuntiva.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Disponibilità non trovata durante il tentativo di cancellazione."
            )

        return None # Per lo status 204, non si restituisce contenuto

    except mariadb.Error:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno durante la cancellazione della disponibilità."
        )
    finally:
        close_db_resources(conn, cursor)

