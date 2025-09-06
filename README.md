# Assistente Virtuale AI per l'Orientamento Sanitario

## Descrizione del Progetto
Questo progetto di tesi mira allo sviluppo di una piattaforma web innovativa: un Assistente Virtuale AI per l'Orientamento Sanitario. L'obiettivo è analizzare i sintomi, fornire indicazioni sanitarie preliminari, indirizzare i pazienti verso lo specialista più adatto, offrire un motore di ricerca geolocalizzato per professionisti sanitari e integrare un sistema di prenotazione e valutazione delle visite.

## Tecnologie Utilizzate
* **Backend:** Python 3.10, FastAPI, MariaDB
* **Intelligenza Artificiale:** 
    * Ollama con modello MedGemma/Llama 3.1
    * LangGraph per orchestrazione agenti AI
    * LangChain per strumenti RAG
    * FAISS per vector store e ricerca semantica
* **Frontend:** HTML5, CSS3, JavaScript ES6+ (con FastAPI per il templating)
* **Containerizzazione:** Docker, Docker Compose (con supporto GPU)
* **Sicurezza:** JWT Authentication, input sanitization, XSS prevention
* **Database:** MariaDB con trigger automatici e gestione transazionale

## Pattern e Utility Introdotte (Refactor 2025)

- `backend/src/utils/database_manager.py`
  - `db_transaction()`: context manager per operazioni in scrittura con commit/rollback automatici.
  - `db_readonly()`: context manager per query di sola lettura con chiusura risorse automatica.
  - Helper profilo utente: `get_doctor_profile_id(...)`, `get_patient_profile_id(...)`, `get_user_profile_data(...)`.

- `backend/src/utils/auth.py`
  - `_load_user_out(user_id)`: recupero profilo centralizzato per `get_current_user` e `get_optional_current_user`.

- `backend/src/utils/auth_decorators.py`
  - Dependency: `get_medico_profile_id`, `get_paziente_profile_id` per iniettare automaticamente l'ID profilo.

- `frontend/templates/static/js/main.js`
  - `callApi(...)`: wrapper fetch con gestione 401.
  - `TypingIndicator`, `SalusNotifier`: UI helpers globali.
  - `escapeHtml(str)`, `sanitizePhone(str)`: sanitizzazione output UI.
  - Autocomplete:
    - `initAddressAutocomplete(...)`: suggerimenti indirizzi da backend.
    - `initSimpleAutocomplete(...)`: autocomplete generico su array in memoria.
  - Chat:
    - `ChatHelpers`: riconoscimento specialista, (dis)abilitazione input, pulsante prenotazione.
    - `ChatAPI`: invio messaggi e reset sessione chat verso backend.
    - `ChatUI`: rendering messaggi e integrazione con `ChatHelpers`.

### Esempi d'uso

```python
# backend (router): lettura
from utils.database_manager import db_readonly

with db_readonly() as cursor:
    cursor.execute("SELECT * FROM Specializzazioni ORDER BY nome ASC")
    specializzazioni = cursor.fetchall()
```

```python
# backend (router): transazione con lock
from utils.database_manager import db_transaction

with db_transaction() as (conn, cursor):
    cursor.execute("SELECT * FROM Disponibilita WHERE id = ? FOR UPDATE", (id_,))
    # ... operazioni ...
```

```html
<!-- frontend: autocomplete semplice -->
<input id="spec-booking-search"><div id="spec-booking-suggestions"></div>
<script>
  initSimpleAutocomplete(
    'spec-booking-search',
    'spec-booking-suggestions',
    () => allSpecializations,
    (spec) => { selectedSpecId = spec.id; },
    (spec) => spec.nome
  );
</script>
```

## Installazione ed Esecuzione
1.  Clonare il repository.
2.  Assicurarsi di avere Docker e Docker Compose installati.
3.  Eseguire il seguente comando dalla cartella principale del progetto:
    ```bash
    docker-compose up --build -d
    ```
4.  L'applicazione sarà accessibile:
    * **Frontend UI:** `http://localhost:8000`
    * **Backend API Docs:** `http://localhost:8001/docs`

## Stato del Progetto
**Fase Attuale:** Sviluppo Frontend Avanzato (In Corso)

### Backend (Completato ✅)
Sono state implementate tutte le logiche di base del backend, tra cui:
* **Architettura Modulare:** Il backend è stato strutturato in `routers` per una maggiore manutenibilità.
* **Gestione Utenti:** API complete per la registrazione e il login di Medici e Pazienti.
* **Sistema di Prenotazione:** Ciclo di vita completo per la gestione delle visite:
    * I medici possono inserire, visualizzare e cancellare le proprie disponibilità.
    * I pazienti possono prenotare gli slot liberi.
    * Lo stato di una prenotazione può essere aggiornato (es. a "Completata").
* **Sistema di Valutazione:** I pazienti possono lasciare una recensione per le visite completate. Il punteggio medio del medico viene ricalcolato automaticamente tramite un `TRIGGER` sul database.
* **Integrazione AI Avanzata:** 
    * Orchestratore LangGraph per analisi sintomi intelligente
    * Strumenti RAG per raccomandazioni specialisti
    * Memoria conversazionale persistente per ogni utente
    * Sistema di tool calling per ricerca medici specializzati
* **Utility:** API per la ricerca di specializzazioni, geocoding e autocomplete degli indirizzi.

### Frontend (In Sviluppo Attivo 🔄)
**Componenti Implementati:**
* **Sistema di Autenticazione:** Pagine complete di login, registrazione medici e pazienti
* **Dashboard Medico:** Interfaccia per visualizzazione e gestione appuntamenti
* **Profilo Utente:** Pagine di gestione profilo per medici e pazienti
* **Ricerca Geolocalizzata:** Sistema di ricerca medici con filtri e mappa interattiva
* **Chat AI:** Interfaccia conversazionale con il chatbot medico integrato
* **Sistema Prenotazioni:** Modulo interattivo per prenotazione appuntamenti
* **Gestione Disponibilità:** Interfaccia per medici per gestire i propri slot
* **Sistema Valutazioni:** Pagine per visualizzare e lasciare recensioni

**Nuove Utility e Helper JS:**
* **API Communication:** Wrapper `callApi()` con gestione automatica 401/logout
* **UI Components:** `TypingIndicator`, `SalusNotifier` per notifiche globali
* **Sicurezza:** `escapeHtml()`, `sanitizePhone()` per prevenire XSS
* **Autocomplete:** Sistema modulare per suggerimenti indirizzi e specializzazioni
* **Chat Helpers:** Integrazione completa con backend AI, riconoscimento specialisti, quick actions

### Refactor e Miglioramenti Recenti:
- **Database Layer:** Context manager `db_transaction()` e `db_readonly()` per gestione connessioni
- **Auth Decorators:** Dependency injection automatica per profili medici/pazienti
- **Code Security:** Sanitizzazione completa HTML dinamico nel frontend
- **Code Reusability:** Helper centralizzati per chat, autocomplete e comunicazione API
- **Frontend Architecture:** Template modulari con base layout e componenti riutilizzabili

## Linee Guida Contributi

- Uso `db_transaction` vs `db_readonly`:
  - `db_transaction`: per operazioni che modificano dati (INSERT/UPDATE/DELETE) e per SELECT con lock (es. `FOR UPDATE`). Si occupa di commit/rollback e chiude le risorse.
  - `db_readonly`: per tutte le SELECT senza side-effect. Non fa commit e chiude sempre le risorse.
- Recupero profilo utente:
  - Per ottenere `UserOut` da token, usa sempre `_load_user_out` (già incapsulato in `get_current_user`/`get_optional_current_user`).
  - Per ottenere `medico_id` o `paziente_id`, preferisci le dependency `get_medico_profile_id`/`get_paziente_profile_id` invece di scrivere query nei router.
- Router FastAPI:
  - Evita boilerplate `conn/cursor`; usa i context manager sopra.
  - Mantieni i lock (`FOR UPDATE`) nelle transazioni quando serve consistenza.
- Frontend JS:
  - Evita `innerHTML` con dati utente; usa `escapeHtml` o costruisci il DOM con `textContent`.
  - Per autocomplete, usa `initAddressAutocomplete` (server-side) o `initSimpleAutocomplete` (client-side array) invece di duplicare logiche.
  - Per la chat usa `ChatHelpers`, `ChatAPI`, `ChatUI`; non duplicare funzioni nei template.

## QA Checklist (aree rifattorizzate)

- Autenticazione
  - Login con credenziali corrette restituisce `UserOut` con `token`.
  - Token scaduto → `callApi` intercetta 401 e forza logout.
- Prenotazioni
  - Paziente: creazione prenotazione su slot libero (stato `Confermata`).
  - Medico: lista prenotazioni personali corretta e ordinata.
  - Patch stato: `Completata` solo da medico proprietario; `Cancellata` da medico o paziente proprietario; slot liberato quando cancellata.
  - Concorrenza: prenotazione doppia dello stesso slot rifiutata (lock + check).
- Valutazioni
  - Paziente può valutare solo prenotazioni `Completata` e proprie; doppia valutazione bloccata (409).
  - Medico: lista valutazioni ordinate per data.
- Ricerca Medici
  - Lista con filtri (`specializzazione_id`, `citta`, `date_disponibili`, `sort_by`).
  - Geolocalizzata: `/medici/vicini` e `/medici/vicini-autenticato` rientrano risultati entro raggio; popup mappa coerenti.
- Frontend UI
  - Autocomplete specializzazione e indirizzo funzionanti (incluso "📍 Vicino a me").
  - Chat: invio messaggi, typing indicator, quick action → risposta AI e pulsante "Prenota ora!" quando rilevata specializzazione.
  - Reset chat: pulizia finestra, rigenerazione `session_id` e riattivazione input.
  - Sanitizzazione: nessun HTML injectabile in nomi/campi dinamici; numeri `tel:` normalizzati.

## Schema del Database
Lo schema Entità-Relazione (ER) del database è disponibile nel seguente file:

[![Schema ER del Database](./docs/schema_ER_DB.svg)](./docs/schema_ER_DB.svg)

## Roadmap
- [x] **Fase 1: Progettazione Architetturale**
    - [x] Definizione dell'architettura Backend e Frontend.
    - [x] Progettazione del Database.
    - [x] Scelta del modello AI.
- [x] **Fase 2: Sviluppo Backend**
    - [x] API per gestione utenti e autenticazione.
    - [x] API per la gestione delle prenotazioni e valutazioni.
    - [x] API per l'analisi dei sintomi e suggerimenti (Integrazione AI).
    - [x] API per la ricerca geolocalizzata di specialisti (Utility).
- [x] **Fase 3: Sicurezza Backend**
    - [x] Implementazione di Authentication e Authorization (JWT) su tutti gli endpoint sensibili.
- [x] **Fase 4: Integrazione AI Avanzata**
    - [x] Implementazione orchestratore LangGraph con memoria conversazionale.
    - [x] Sviluppo strumenti RAG per ricerca specialisti medici.
    - [x] Sistema di tool calling per raccomandazioni intelligenti.
- [x] **Fase 5: Sviluppo Frontend Core**
    - [x] Interfaccia utente per la registrazione e il login.
    - [x] Interfaccia per la ricerca geolocalizzata e la visualizzazione dei profili medici.
    - [x] Modulo di prenotazione interattivo.
    - [x] Sezione per la gestione del proprio profilo e delle proprie prenotazioni/valutazioni.
    - [x] Dashboard medico per gestione appuntamenti e disponibilità.
    - [x] Sistema di chat AI con interfaccia utente completa.
- [x] **Fase 6: Refactor e Ottimizzazione**
    - [x] Implementazione pattern database con context manager.
    - [x] Centralizzazione helper JavaScript e utility API.
    - [x] Sanitizzazione sicurezza frontend (prevenzione XSS).
    - [x] Modularizzazione architettura frontend con componenti riutilizzabili.
- [ ] **Fase 7: Finalizzazione e Polish**
    - [ ] Completamento interfacce utente con feedback UX.
    - [ ] Ottimizzazione performance e responsività mobile.
    - [ ] Miglioramento gestione errori e validazione input.
- [ ] **Fase 8: Testing e Distribuzione**
    - [ ] Test unitari e di integrazione completi.
    - [ ] Test end-to-end delle funzionalità critiche.
    - [ ] Debugging finale e ottimizzazione delle performance.
    - [ ] Preparazione per la distribuzione in produzione.

## Contributi
Questo progetto è sviluppato da [tremorz3] e [raaiss].

## Contatti
- [Giovanni] - [pinto.2046796@studenti.uniroma1.it]
- [Raimondo] - [massari.2067064@studenti.uniroma1.it]
