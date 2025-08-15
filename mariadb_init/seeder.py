import mariadb
import os
from dotenv import load_dotenv
from faker import Faker
import random
from datetime import datetime, timedelta
import sys

# --- CONFIGURAZIONE ---
# Carica le variabili d'ambiente dal file .env che si trova nella root del progetto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Numero di record da generare
NUM_PAZIENTI = 150
NUM_MEDICI = 50
MIN_DISPONIBILITA_PER_MEDICO = 20
MAX_DISPONIBILITA_PER_MEDICO = 100
PERCENTUALE_PRENOTAZIONI = 75 # Percentuale di slot disponibili che verranno prenotati
PERCENTUALE_VALUTAZIONI = 80 # Percentuale di prenotazioni completate che riceveranno una valutazione

# Password hash per "password123" (preso dal tuo seeding.sql originale)
PWD_HASH = '$2b$12$isOKlAZsvw8CkSOsugAQ7uvhtoEZVqOCH.T0zPF3PqO0UPE68ngbC'

# Inizializza Faker per dati italiani
fake = Faker('it_IT')

def get_db_connection():
    """Crea e restituisce una connessione al database MariaDB."""
    try:
        conn = mariadb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME")
        )
        return conn
    except mariadb.Error as e:
        print(f"Errore di connessione al database: {e}")
        sys.exit(1)

def tabelle_sono_vuote(cursor):
    """Controlla se la tabella Utenti è vuota."""
    cursor.execute("SELECT COUNT(id) FROM Utenti")
    count = cursor.fetchone()[0]
    if count > 0:
        print("Il database sembra essere già popolato. Lo script di seeding non verrà eseguito.")
        return False
    return True

def crea_medici_test(cursor, specializzazioni_ids):
    """Crea 3 medici con dati reali a Roma per testare la geolocalizzazione."""
    print("Creazione di 3 medici di test a Roma...")
    medici_test = [
        {
            "nome": "Mario", "cognome": "Rossi", "email": "dott.mario.rossi@clinic.com",
            "citta": "Roma", "indirizzo": "Piazza del Colosseo, 1, 00184 Roma RM",
            "lat": 41.8902, "lon": 12.4922, "spec_id": 10 # Cardiologia
        },
        {
            "nome": "Giulia", "cognome": "Bianchi", "email": "dott.giulia.bianchi@clinic.com",
            "citta": "Roma", "indirizzo": "Piazza della Rotonda, 00186 Roma RM",
            "lat": 41.8986, "lon": 12.4769, "spec_id": 18 # Dermatologia
        },
        {
            "nome": "Luca", "cognome": "Verdi", "email": "dott.luca.verdi@clinic.com",
            "citta": "Roma", "indirizzo": "Via della Conciliazione, 00193 Roma RM",
            "lat": 41.9022, "lon": 12.4589, "spec_id": 44 # Ortopedia
        }
    ]

    medici_ids_test = []
    for medico in medici_test:
        cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'medico')", (medico["email"], PWD_HASH))
        utente_id = cursor.lastrowid
        
        medico_values = (
            utente_id, medico["spec_id"], medico["nome"], medico["cognome"], medico["citta"],
            fake.msisdn()[:10], f"Ordine dei Medici di Roma", fake.numerify('#####'),
            'RM', medico["indirizzo"], medico["lat"], medico["lon"]
        )
        cursor.execute("""
            INSERT INTO Medici (utente_id, specializzazione_id, nome, cognome, citta, telefono, 
                                ordine_iscrizione, numero_iscrizione, provincia_iscrizione, 
                                indirizzo_studio, latitudine, longitudine) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, medico_values)
        medici_ids_test.append(cursor.lastrowid)
    return medici_ids_test


def genera_dati():
    """Funzione principale per generare e inserire tutti i dati."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # CONTROLLO PRELIMINARE: esegui solo se il DB è vuoto
        if not tabelle_sono_vuote(cursor):
            return

        print("Il database è vuoto. Inizio del processo di seeding...")
        conn.begin() # Inizia una transazione

        # --- 1. SPECIALIZZAZIONI ---
        cursor.execute("SELECT id FROM Specializzazioni")
        specializzazioni_ids = [row[0] for row in cursor.fetchall()]
        if not specializzazioni_ids:
            print("Nessuna specializzazione trovata. Assicurati di eseguire init.sql prima.")
            return

        # --- 2. PAZIENTI ---
        print(f"Creazione di {NUM_PAZIENTI} pazienti...")
        pazienti_ids = []
        for _ in range(NUM_PAZIENTI):
            nome = fake.first_name()
            cognome = fake.last_name()
            email = f"{nome.lower()}.{cognome.lower()}@email.com"
            telefono = fake.msisdn()[:10]

            cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'paziente')", (email, PWD_HASH))
            utente_id = cursor.lastrowid
            cursor.execute("INSERT INTO Pazienti (utente_id, nome, cognome, telefono) VALUES (?, ?, ?, ?)", (utente_id, nome, cognome, telefono))
            pazienti_ids.append(cursor.lastrowid)

        # --- 3. MEDICI ---
        medici_ids = crea_medici_test(cursor, specializzazioni_ids)

        # Generiamo i medici casuali (ridotti di 3 per mantenere il totale)
        print(f"Creazione di {NUM_MEDICI - 3} medici...")
        medici_ids = []
        for _ in range(NUM_MEDICI - 3):
            nome = fake.first_name()
            cognome = fake.last_name()
            email = f"dott.{nome.lower()}.{cognome.lower()}@clinic.com"
            citta = fake.city()
            
            cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'medico')", (email, PWD_HASH))
            utente_id = cursor.lastrowid
            
            medico_values = (
                utente_id, random.choice(specializzazioni_ids), nome, cognome, citta,
                fake.msisdn()[:10], f"Ordine dei Medici di {citta}", fake.numerify('#####'),
                fake.state_abbr(), fake.street_address(), float(fake.latitude()), float(fake.longitude())
            )
            cursor.execute("""
                INSERT INTO Medici (utente_id, specializzazione_id, nome, cognome, citta, telefono, 
                                    ordine_iscrizione, numero_iscrizione, provincia_iscrizione, 
                                    indirizzo_studio, latitudine, longitudine) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, medico_values)
            medici_ids.append(cursor.lastrowid)
            
        # --- 4. DISPONIBILITÀ, PRENOTAZIONI E VALUTAZIONI ---
        print("Creazione di disponibilità, prenotazioni e valutazioni...")
        now = datetime.now()
        prenotazioni_completate = []

        for medico_id in medici_ids:
            num_disponibilita = random.randint(MIN_DISPONIBILITA_PER_MEDICO, MAX_DISPONIBILITA_PER_MEDICO)
            for _ in range(num_disponibilita):
                # 50% di possibilità di creare una disponibilità nel passato
                if random.random() < 0.5:
                    start_date = now - timedelta(days=random.randint(1, 180), hours=random.randint(0, 23), minutes=random.choice([0, 30]))
                else:
                    start_date = now + timedelta(days=random.randint(1, 90), hours=random.randint(0, 23), minutes=random.choice([0, 30]))
                
                end_date = start_date + timedelta(minutes=30)
                
                # Inserisci la disponibilità
                cursor.execute("INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine) VALUES (?, ?, ?)",
                               (medico_id, start_date, end_date))
                disponibilita_id = cursor.lastrowid

                # Decidi se prenotare questo slot
                if random.randint(1, 100) <= PERCENTUALE_PRENOTAZIONI:
                    paziente_id = random.choice(pazienti_ids)
                    
                    stato = 'Confermata'
                    if start_date < now:
                         # Eventi passati possono essere 'Completata' o 'Cancellata'
                        stato = random.choice(['Completata', 'Completata', 'Completata', 'Cancellata']) # Più probabilità che sia completata
                    
                    note = fake.sentence(nb_words=10) if random.random() < 0.6 else None
                    
                    cursor.execute("INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato, note_paziente) VALUES (?, ?, ?, ?)",
                                   (disponibilita_id, paziente_id, stato, note))
                    prenotazione_id = cursor.lastrowid
                    
                    # Segna la disponibilità come prenotata
                    cursor.execute("UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = ?", (disponibilita_id,))
                    
                    if stato == 'Completata':
                        prenotazioni_completate.append({
                            "id": prenotazione_id,
                            "paziente_id": paziente_id,
                            "medico_id": medico_id
                        })

        # --- 5. VALUTAZIONI (basate sulle prenotazioni completate) ---
        num_valutazioni = int(len(prenotazioni_completate) * (PERCENTUALE_VALUTAZIONI / 100))
        prenotazioni_da_valutare = random.sample(prenotazioni_completate, num_valutazioni)
        
        print(f"Creazione di {len(prenotazioni_da_valutare)} valutazioni...")
        for p in prenotazioni_da_valutare:
            punteggio = random.randint(3, 5) # I medici tendono ad avere buone recensioni
            commento = fake.paragraph(nb_sentences=3) if random.random() < 0.7 else None
            cursor.execute("INSERT INTO Valutazioni (prenotazione_id, paziente_id, medico_id, punteggio, commento) VALUES (?, ?, ?, ?, ?)",
                           (p['id'], p['paziente_id'], p['medico_id'], punteggio, commento))

        # --- Conclusione ---
        conn.commit() # Rendi permanenti tutte le modifiche
        print("\nSeeding completato con successo!")

    except mariadb.Error as e:
        print(f"\nErrore durante il seeding: {e}")
        print("Rollback delle modifiche in corso...")
        conn.rollback() # Annulla tutte le operazioni in caso di errore
    finally:
        print("Chiusura della connessione al database.")
        cursor.close()
        conn.close()


if __name__ == "__main__":
    genera_dati()