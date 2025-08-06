# Assistente Virtuale AI per l'Orientamento Sanitario

## Descrizione del Progetto
Questo progetto di tesi mira allo sviluppo di una piattaforma web innovativa: un Assistente Virtuale AI per l'Orientamento Sanitario. L'obiettivo è analizzare i sintomi, fornire indicazioni sanitarie preliminari, indirizzare i pazienti verso lo specialista più adatto, offrire un motore di ricerca geolocalizzato per professionisti sanitari e integrare un sistema di prenotazione e valutazione delle visite.

## Tecnologie Utilizzate
* **Backend:** Python 3.10, FastAPI, MariaDB
* **Intelligenza Artificiale:** Ollama con modello MedGemma
* **Containerizzazione:** Docker, Docker Compose
* **Frontend:** HTML5, CSS3, JavaScript (con FastAPI per il templating)

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
**Fase Attuale:** Sviluppo Funzionalità Backend (Completato)

Sono state implementate tutte le logiche di base del backend, tra cui:
* **Architettura Modulare:** Il backend è stato strutturato in `routers` per una maggiore manutenibilità.
* **Gestione Utenti:** API complete per la registrazione e il login di Medici e Pazienti.
* **Sistema di Prenotazione:** Ciclo di vita completo per la gestione delle visite:
    * I medici possono inserire, visualizzare e cancellare le proprie disponibilità.
    * I pazienti possono prenotare gli slot liberi.
    * Lo stato di una prenotazione può essere aggiornato (es. a "Completata").
* **Sistema di Valutazione:** I pazienti possono lasciare una recensione per le visite completate. Il punteggio medio del medico viene ricalcolato automaticamente tramite un `TRIGGER` sul database.
* **Integrazione AI:** Endpoint per la chat con il modello AI.
* **Utility:** API per la ricerca di specializzazioni e autocomplete degli indirizzi.

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
- [ ] **Fase 3: Sicurezza Backend**
    - [ ] Implementazione di Authentication e Authorization (JWT) su tutti gli endpoint sensibili.
- [ ] **Fase 4: Sviluppo Frontend**
    - [ ] Interfaccia utente per la registrazione e il login.
    - [ ] Interfaccia per la ricerca geolocalizzata e la visualizzazione dei profili medici.
    - [ ] Modulo di prenotazione interattivo.
    - [ ] Sezione per la gestione del proprio profilo e delle proprie prenotazioni/valutazioni.
- [ ] **Fase 5: Testing e Distribuzione**
    - [ ] Test unitari e di integrazione.
    - [ ] Debugging e ottimizzazione delle performance.
    - [ ] Preparazione per la distribuzione.

## Contributi
Questo progetto è sviluppato da [tremorz3] e [raaiss].

## Contatti
- [Giovanni] - [pinto.2046796@studenti.uniroma1.it]
- [Raimondo] - [massari.2067064@studenti.uniroma1.it]
