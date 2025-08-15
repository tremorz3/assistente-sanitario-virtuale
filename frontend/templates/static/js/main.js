/**
 * =================================================================================
 * Assistente Virtuale Sanitario - Script Principale (main.js)
 * =================================================================================
 * Questo file gestisce la logica globale del frontend, tra cui:
 * 1. Gestione dinamica della barra di navigazione in base al ruolo dell'utente.
 * 2. Funzioni helper per le chiamate API sicure.
 * 3. Funzionalità di logout.
 * =================================================================================
 */

/**
 * Funzione eseguita al caricamento completo del DOM.
 * È il punto di ingresso di tutta la nostra logica frontend.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Funzione per aggiornare la UI della navbar
    updateNavbar();

    // Aggiungiamo l'evento al pulsante di logout, se esiste
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', (e) => {
            e.preventDefault(); // Preveniamo il comportamento di default del link
            logout();
        });
    }
});

/**
 * =================================================================================
 * SalusNotifier - Sistema di Notifiche Personalizzato
 * =================================================================================
 */
const SalusNotifier = {
    // Elementi del DOM del modale
    overlay: document.getElementById('salus-notifier-overlay'),
    titleElem: document.getElementById('salus-notifier-title'),
    messageElem: document.getElementById('salus-notifier-message'),
    buttonsElem: document.getElementById('salus-notifier-buttons'),

    /**
     * Mostra una notifica di tipo "alert" (con un solo pulsante "OK").
     * @param {string} message - Il messaggio da mostrare.
     * @param {string} title - Il titolo del modale.
     */
    alert: function(message, title = 'Notifica') {
        this.titleElem.textContent = title;
        this.messageElem.textContent = message;
        
        // Pulisce i pulsanti precedenti e aggiunge solo "OK"
        this.buttonsElem.innerHTML = '';
        const okButton = document.createElement('button');
        okButton.textContent = 'OK';
        okButton.className = 'notifier-btn-confirm';
        okButton.onclick = () => this.hide();
        
        this.buttonsElem.appendChild(okButton);
        this.show();
    },

    /**
     * Mostra una notifica di tipo "confirm" (con pulsanti Conferma e Annulla).
     * @param {string} message - Il messaggio di conferma.
     * @param {string} title - Il titolo del modale.
     * @returns {Promise<boolean>} - Una Promise che si risolve a `true` se l'utente
     * conferma, `false` altrimenti.
     */
    confirm: function(message, title = 'Sei sicuro?') {
        this.titleElem.textContent = title;
        this.messageElem.textContent = message;
        this.buttonsElem.innerHTML = '';

        // La Promise è il cuore del sistema non bloccante
        return new Promise(resolve => {
            const confirmButton = document.createElement('button');
            confirmButton.textContent = 'Conferma';
            confirmButton.className = 'notifier-btn-confirm';
            confirmButton.onclick = () => {
                this.hide();
                resolve(true); // L'utente ha confermato
            };

            const cancelButton = document.createElement('button');
            cancelButton.textContent = 'Annulla';
            cancelButton.className = 'notifier-btn-cancel';
            cancelButton.onclick = () => {
                this.hide();
                resolve(false); // L'utente ha annullato
            };

            this.buttonsElem.appendChild(cancelButton);
            this.buttonsElem.appendChild(confirmButton);
            this.show();
        });
    },

    // Funzioni helper per mostrare e nascondere il modale
    show: function() { this.overlay.classList.remove('hidden'); },
    hide: function() { this.overlay.classList.add('hidden'); }
};

// Aggiungiamo un listener per chiudere il modale se si clicca sull'overlay
SalusNotifier.overlay.addEventListener('click', (e) => {
    if (e.target === SalusNotifier.overlay) {
        SalusNotifier.hide();
    }
});

/**
 * Aggiorna la visibilità degli elementi nella barra di navigazione
 * in base allo stato di login dell'utente.
 */
/**
 * Aggiorna la visibilità degli elementi nella barra di navigazione
 * in base allo stato di login e al ruolo dell'utente.
 * Questa versione è più robusta perché imposta esplicitamente lo stato
 * di ogni link invece di nasconderli tutti e poi mostrarne alcuni.
 */
function updateNavbar() {
    const token = localStorage.getItem('user_token');
    const isLoggedIn = !!token;
    let userType = null;

    // Se l'utente è loggato, decodifichiamo il token per ottenere il suo ruolo
    if (isLoggedIn) {
        try {
            userType = parseJwt(token).tipo_utente;
        } catch (error) {
            console.error("Token non valido o malformato, logout forzato.", error);
            logout(); // Se il token non è valido, eseguiamo il logout e interrompiamo la funzione
            return;
        }
    }

    // Selezioniamo gli elementi della navbar
    const navLogo = document.querySelector('.nav-logo');
    const navItems = {
        login: document.getElementById('nav-login'),
        registerPaziente: document.getElementById('nav-register-paziente'),
        registerMedico: document.getElementById('nav-register-medico'),
        cercaMedici: document.getElementById('nav-cerca-medici'),
        profiloPaziente: document.getElementById('nav-profilo-paziente'),
        dashboardMedico: document.getElementById('nav-dashboard-medico'),
        gestioneDisponibilita: document.getElementById('nav-gestione-disponibilita'),
        recensioniMedico: document.getElementById('nav-recensioni-medico'),
        logout: document.getElementById('nav-logout')
    };

    // La funzione classList.toggle(classe, condizione) è perfetta per questo:
    // aggiunge la classe 'hidden' se la condizione è VERA, la rimuove se è FALSA.

    // Link di autenticazione: visibili solo se l'utente NON è loggato
    navItems.login?.classList.toggle('hidden', isLoggedIn);
    navItems.registerPaziente?.classList.toggle('hidden', isLoggedIn);
    navItems.registerMedico?.classList.toggle('hidden', isLoggedIn);

    // Link di logout: visibile solo se l'utente È loggato
    navItems.logout?.classList.toggle('hidden', !isLoggedIn);

    // === MODIFICA CHIAVE ===
    // Link "I Nostri Medici": visibile a TUTTI (la condizione per nasconderlo è sempre falsa)
    navItems.cercaMedici?.classList.toggle('hidden', false);

    // Link specifici per il PAZIENTE
    navItems.profiloPaziente?.classList.toggle('hidden', userType !== 'paziente');

    // Link specifici per il MEDICO
    navItems.dashboardMedico?.classList.toggle('hidden', userType !== 'medico');
    navItems.gestioneDisponibilita?.classList.toggle('hidden', userType !== 'medico');
    navItems.recensioniMedico?.classList.toggle('hidden', userType !== 'medico');
    
    // Logica per il link del logo
    if (navLogo) {
        if (userType === 'medico') {
            navLogo.href = '/dashboard-medico';
        } else {
            // Per pazienti e utenti non loggati, punta alla home
            navLogo.href = '/';
        }
    }
}

/**
 * Decodifica un token JWT per estrarne il payload (i dati).
 * @param {string} token - Il token JWT da decodificare.
 * @returns {object} - L'oggetto payload del token.
 */
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1]; // Prendiamo il payload
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        throw new Error("Token non valido o malformato.");
    }
}

/**
 * Esegue il logout dell'utente.
 */
function logout() {
    localStorage.removeItem('user_token'); // Rimuove il token
    window.location.href = '/pagina-login'; // Reindirizza al login
}

/**
 * Funzione helper per effettuare chiamate API sicure.
 * Aggiunge il token JWT e gestisce gli errori 401 (Unauthorized).
 * @param {string} endpoint - L'URL dell'API da chiamare.
 * @param {object} options - Opzioni per la richiesta `fetch` (method, headers, body).
 * @returns {Promise<object>} - I dati JSON della risposta.
 */
async function callApi(endpoint, options = {}) {
    const token = localStorage.getItem('user_token');
    
    const headers = options.headers || {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    options.headers = headers;

    const response = await fetch(endpoint, options);

    if (response.status === 401) {
        console.log("Token non valido o scaduto. Eseguo il logout.");
        logout();
        throw new Error('Sessione scaduta. Effettua nuovamente il login.');
    }
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Errore HTTP: ${response.status}` }));
        throw new Error(errorData.detail);
    }

    return response.status === 204 ? {} : response.json();
}