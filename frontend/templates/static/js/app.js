/**
 * Funzione helper globale per effettuare chiamate API autenticate.
 * Aggiunge automaticamente il token JWT e gestisce gli errori di autenticazione.
 * @param {string} endpoint - L'endpoint API da chiamare (es. '/me').
 * @param {object} options - Le opzioni per la richiesta fetch (es. method, body, headers).
 * @returns {Promise<object>} - I dati JSON della risposta.
 */
async function callApi(endpoint, options = {}) {
    const token = localStorage.getItem('user_token');
    
    // Inizializziamo gli headers; se non esistono, creiamo un oggetto vuoto.
    const headers = options.headers || {};
    
    if (token) {
        // Se abbiamo un token, lo aggiungiamo all'header Authorization.
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Aggiungiamo gli headers aggiornati alle opzioni della richiesta.
    options.headers = headers;

    const response = await fetch(endpoint, options);

    // GESTIONE TOKEN SCADUTO: questo è il cuore della gestione della sessione.
    if (response.status === 401) {
        // Se il backend ci dice che non siamo autorizzati, il token è
        // probabilmente scaduto o non valido.
        console.log("Token non valido o scaduto. Eseguo il logout.");
        logout(); // Eseguiamo il logout forzato.
        // Blocchiamo l'esecuzione per evitare altri errori.
        throw new Error('Sessione scaduta');
    }
    
    if (!response.ok) {
        // Gestiamo altri errori del server.
        const errorData = await response.json();
        throw new Error(errorData.detail || `Errore HTTP: ${response.status}`);
    }

    // Se la risposta non ha contenuto (es. DELETE 204), restituiamo un oggetto vuoto.
    if (response.status === 204) {
        return {};
    }

    return response.json();
}

/**
 * Funzione per effettuare il logout dell'utente.
 */
function logout() {
    // Rimuoviamo il token dal localStorage.
    localStorage.removeItem('user_token');
    // Reindirizziamo l'utente alla pagina di login.
    window.location.href = '/pagina-login';
}