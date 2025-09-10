import mariadb
import os
from dotenv import load_dotenv
from faker import Faker
import random
from datetime import datetime, timedelta
import sys
import json
from shapely.geometry import shape, Point

# --- CONFIGURAZIONE ---
# Carica le variabili d'ambiente dal file .env che si trova nella root del progetto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Numero di record da generare
NUM_PAZIENTI = 150
# Aggiornato per riflettere i 10 medici di test + 1 admin
NUM_MEDICI = 50 
MIN_DISPONIBILITA_PER_MEDICO = 20
MAX_DISPONIBILITA_PER_MEDICO = 100
PERCENTUALE_PRENOTAZIONI = 75 # Percentuale di slot disponibili che verranno prenotati
PERCENTUALE_VALUTAZIONI = 80 # Percentuale di prenotazioni completate che riceveranno una valutazione

# Password hash per "password123"
PWD_HASH = '$2b$12$isOKlAZsvw8CkSOsugAQ7uvhtoEZVqOCH.T0zPF3PqO0UPE68ngbC'

# Faker inizializzato per dati italiani
fake = Faker('it_IT')

# --- NUOVA LOGICA GEOGRAFICA ---
italy_shape = None
try:
    geojson_path = os.path.join(os.path.dirname(__file__), 'italia_confini.geojson')
    with open(geojson_path) as f:
        geojson_data = json.load(f)
    
    # Crea una singola geometria unificata per tutta l'Italia
    polygons = [shape(feature['geometry']) for feature in geojson_data['features']]
    italy_shape = polygons[0]
    for p in polygons[1:]:
        italy_shape = italy_shape.union(p)

    # Bounding box per la generazione di punti casuali
    MIN_LON, MIN_LAT, MAX_LON, MAX_LAT = italy_shape.bounds

except Exception as e:
    print(f"ATTENZIONE: Impossibile caricare i confini geografici da 'italia_confini.geojson': {e}")
    print("Le coordinate dei medici verranno generate in un rettangolo approssimativo.")
    MIN_LAT, MAX_LAT = 36.0, 47.0
    MIN_LON, MAX_LON = 6.0, 19.0


def get_random_point_in_italy():
    """
    Genera un punto di coordinate casuale che cade ENTRO i confini italiani.
    """
    if not italy_shape: # Fallback se il file geojson non è stato caricato
        return random.uniform(MIN_LAT, MAX_LAT), random.uniform(MIN_LON, MAX_LON)
        
    while True:
        # Genera un punto casuale all'interno del rettangolo di delimitazione
        random_point = Point(random.uniform(MIN_LON, MAX_LON), random.uniform(MIN_LAT, MAX_LAT))
        
        # Controlla se il punto è effettivamente dentro la forma dell'Italia
        if italy_shape.contains(random_point):
            return random_point.y, random_point.x # Ritorna (latitudine, longitudine)


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

def crea_utenti_admin(cursor, specializzazioni_ids):
    """Crea un utente paziente e un utente medico fissi per il testing e restituisce il loro id."""
    print("Creazione degli utenti admin di test...")
    paziente_admin_id = None
    medico_admin_id = None
    
    # 1. Crea Paziente Admin
    try:
        email_paziente = "paziente@admin.com"
        cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'paziente')", (email_paziente, PWD_HASH))
        utente_paziente_id = cursor.lastrowid
        cursor.execute("INSERT INTO Pazienti (utente_id, nome, cognome, telefono) VALUES (?, ?, ?, ?)", (utente_paziente_id, "Admin", "Paziente", "1234567890"))
        paziente_admin_id = cursor.lastrowid
        print(f"- Creato utente Paziente Admin con email: {email_paziente}")
    except mariadb.IntegrityError:
        print(f"- Utente Paziente Admin con email {email_paziente} esiste già.")
        cursor.execute("SELECT id FROM Pazienti WHERE utente_id = (SELECT id FROM Utenti WHERE email=?)", (email_paziente,))
        paziente_admin_id = cursor.fetchone()[0]

    # 2. Crea Medico Admin
    try:
        email_medico = "medico@admin.com"
        cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'medico')", (email_medico, PWD_HASH))
        utente_medico_id = cursor.lastrowid
        
        # Specializzazione a caso per il medico admin
        spec_id_admin = random.choice(specializzazioni_ids)

        medico_values = (
            utente_medico_id, spec_id_admin, "Admin", "Medico", "Milano",
            "0987654321", "Ordine dei Medici di Milano", "99999",
            'MI', "Via dei Test, 1, 20121 Milano MI", 45.4642, 9.1900
        )
        cursor.execute("""
            INSERT INTO Medici (utente_id, specializzazione_id, nome, cognome, citta, telefono, 
                                ordine_iscrizione, numero_iscrizione, provincia_iscrizione, 
                                indirizzo_studio, latitudine, longitudine) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, medico_values)
        medico_admin_id = cursor.lastrowid 
        print(f"- Creato utente Medico Admin con email: {email_medico}")
    except mariadb.IntegrityError:
        print(f"- Utente Medico Admin con email {email_medico} esiste già.")
        cursor.execute("SELECT id FROM Medici WHERE utente_id = (SELECT id FROM Utenti WHERE email=?)", (email_medico,))
        medico_admin_id = cursor.fetchone()[0]

    return paziente_admin_id, medico_admin_id

def crea_medici_test(cursor, specializzazioni_ids):
    """Crea 10 medici con dati reali a Roma per testare la geolocalizzazione con le specializzazioni più comuni."""
    print("Creazione di 10 medici di test a Roma...")
    medici_test = [
        {"nome": "Maria", "cognome": "Russo", "spec_id": 6, "lat": 41.9028, "lon": 12.4964}, # Cardiologia
        {"nome": "Francesco", "cognome": "Ferrari", "spec_id": 12, "lat": 41.8919, "lon": 12.5113}, # Dermatologia
        {"nome": "Anna", "cognome": "Romano", "spec_id": 38, "lat": 41.8931, "lon": 12.4829}, # Pediatria
        {"nome": "Marco", "cognome": "Ricci", "spec_id": 33, "lat": 41.9109, "lon": 12.4769}, # Oculistica
        {"nome": "Elena", "cognome": "Conti", "spec_id": 31, "lat": 41.8724, "lon": 12.4801}, # Neurologia
        {"nome": "Giovanni", "cognome": "Galli", "spec_id": 32, "lat": 41.9056, "lon": 12.4573}, # Odontoiatria e Ortodonzia
        {"nome": "Sofia", "cognome": "Colombo", "spec_id": 20, "lat": 41.8986, "lon": 12.4768}, # Gastroenterologia
        {"nome": "Alessandro", "cognome": "Marino", "spec_id": 28, "lat": 41.9022, "lon": 12.4549}, # Medico di Medicina Generale
        {"nome": "Laura", "cognome": "Greco", "spec_id": 22, "lat": 41.8828, "lon": 12.4853}, # Ginecologia
        {"nome": "Paolo", "cognome": "Lombardi", "spec_id": 35, "lat": 41.8947, "lon": 12.4922} # Ortopedia
    ]

    medici_ids_test = []
    for medico in medici_test:
        nome_lower = medico["nome"].lower()
        cognome_lower = medico["cognome"].lower()
        email = f"dott.{nome_lower}.{cognome_lower}@clinic-roma.com"
        
        cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'medico')", (email, PWD_HASH))
        utente_id = cursor.lastrowid
        
        medico_values = (
            utente_id, medico["spec_id"], medico["nome"], medico["cognome"], "Roma",
            fake.msisdn()[:10], "Ordine dei Medici di Roma", fake.numerify('#####'),
            'RM', fake.street_address(), medico["lat"], medico["lon"]
        )
        cursor.execute("""
            INSERT INTO Medici (utente_id, specializzazione_id, nome, cognome, citta, telefono, 
                                ordine_iscrizione, numero_iscrizione, provincia_iscrizione, 
                                indirizzo_studio, latitudine, longitudine) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, medico_values)
        medici_ids_test.append(cursor.lastrowid)
    print(f"- Creati {len(medici_ids_test)} medici di test.")
    return medici_ids_test


def genera_dati():
    """Funzione principale per generare e inserire tutti i dati."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # CONTROLLO PRELIMINARE: funzione eseguita solo se il DB è vuoto
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
        
        # Crea utenti admin fissi
        paziente_admin_id, medico_admin_id = crea_utenti_admin(cursor, specializzazioni_ids)

        # --- 2. PAZIENTI ---
        # Ridotto il numero di pazienti di 1 per fare spazio al paziente admin
        print(f"Creazione di {NUM_PAZIENTI - 1} pazienti...")
        for _ in range(NUM_PAZIENTI - 1):
            nome = fake.first_name()
            cognome = fake.last_name()
            email = f"{nome.lower()}.{cognome.lower()}@email.com"
            telefono = fake.msisdn()[:10]

            cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'paziente')", (email, PWD_HASH))
            utente_id = cursor.lastrowid
            cursor.execute("INSERT INTO Pazienti (utente_id, nome, cognome, telefono) VALUES (?, ?, ?, ?)", (utente_id, nome, cognome, telefono))

        # --- 3. MEDICI ---
        crea_medici_test(cursor, specializzazioni_ids)

        # Generazione medici casuali (ridotti di 11 = 10 di test + 1 admin)
        print(f"Creazione di {NUM_MEDICI - 11} medici...")
        for _ in range(NUM_MEDICI - 11):
            nome = fake.first_name()
            cognome = fake.last_name()
            email = f"dott.{nome.lower()}.{cognome.lower()}@clinic.com"
            citta = fake.city()
            
            cursor.execute("INSERT INTO Utenti (email, password_hash, tipo_utente) VALUES (?, ?, 'medico')", (email, PWD_HASH))
            utente_id = cursor.lastrowid

            # --- Generazione coordinate in Italia ---
            latitudine_italia, longitudine_italia = get_random_point_in_italy()
            
            medico_values = (
                utente_id, random.choice(specializzazioni_ids), nome, cognome, citta,
                fake.msisdn()[:10], f"Ordine dei Medici di {citta}", fake.numerify('#####'),
                fake.state_abbr(), fake.street_address(), latitudine_italia, longitudine_italia
            )
            cursor.execute("""
                INSERT INTO Medici (utente_id, specializzazione_id, nome, cognome, citta, telefono, 
                                    ordine_iscrizione, numero_iscrizione, provincia_iscrizione, 
                                    indirizzo_studio, latitudine, longitudine) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, medico_values)
            
        # --- 4. DISPONIBILITÀ, PRENOTAZIONI E VALUTAZIONI ---
        print("Creazione di disponibilità, prenotazioni e valutazioni...")
        now = datetime.now()
        prenotazioni_completate = []

        # --- Seleziona solo gli ID dei medici NON admin ---
        cursor.execute("SELECT id FROM Medici WHERE id != ?", (medico_admin_id,))
        medici_non_admin_ids = [row[0] for row in cursor.fetchall()]

        # --- Seleziona solo gli ID dei pazienti NON admin ---
        cursor.execute("SELECT id FROM Pazienti WHERE id != ?", (paziente_admin_id,))
        pazienti_non_admin_ids = [row[0] for row in cursor.fetchall()]

        if not medici_non_admin_ids or not pazienti_non_admin_ids:
            print("Nessun utente non-admin trovato per generare dati casuali. Salto questa fase.")
        else:
            for medico_id in medici_non_admin_ids:
                num_disponibilita = random.randint(MIN_DISPONIBILITA_PER_MEDICO, MAX_DISPONIBILITA_PER_MEDICO)
                for _ in range(num_disponibilita):
                    if random.random() < 0.5:
                        start_date = now - timedelta(days=random.randint(1, 180), hours=random.randint(0, 23), minutes=random.choice([0, 30]))
                    else:
                        start_date = now + timedelta(days=random.randint(1, 90), hours=random.randint(0, 23), minutes=random.choice([0, 30]))
                    
                    end_date = start_date + timedelta(minutes=30)
                    
                    cursor.execute("INSERT INTO Disponibilita (medico_id, data_ora_inizio, data_ora_fine) VALUES (?, ?, ?)",
                                   (medico_id, start_date, end_date))
                    disponibilita_id = cursor.lastrowid

                    if random.randint(1, 100) <= PERCENTUALE_PRENOTAZIONI:
                        paziente_id = random.choice(pazienti_non_admin_ids)
                        
                        stato = 'Confermata'
                        if start_date < now:
                            stato = random.choice(['Completata', 'Completata', 'Completata', 'Cancellata'])
                        
                        note = fake.sentence(nb_words=10) if random.random() < 0.6 else None
                        
                        cursor.execute("INSERT INTO Prenotazioni (disponibilita_id, paziente_id, stato, note_paziente) VALUES (?, ?, ?, ?)",
                                       (disponibilita_id, paziente_id, stato, note))
                        prenotazione_id = cursor.lastrowid
                        
                        cursor.execute("UPDATE Disponibilita SET is_prenotato = TRUE WHERE id = ?", (disponibilita_id,))
                        
                        if stato == 'Completata':
                            prenotazioni_completate.append({
                                "id": prenotazione_id,
                                "paziente_id": paziente_id,
                                "medico_id": medico_id
                            })

        # --- 5. VALUTAZIONI (basate sulle prenotazioni completate) ---
        if prenotazioni_completate:
                num_valutazioni = int(len(prenotazioni_completate) * (PERCENTUALE_VALUTAZIONI / 100))
                prenotazioni_da_valutare = random.sample(prenotazioni_completate, num_valutazioni)
                
                print(f"Creazione di {len(prenotazioni_da_valutare)} valutazioni...")
                for p in prenotazioni_da_valutare:
                    punteggio = random.randint(3, 5)
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