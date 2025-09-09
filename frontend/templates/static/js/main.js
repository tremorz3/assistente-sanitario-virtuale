/**
 * =================================================================================
 * Assistente Virtuale Sanitario - Script Principale (main.js) - Updated
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
    // ========= LOGICA PER HAMBURGER MENU =========
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            // Aggiunge/rimuove la classe per mostrare il menu
            navMenu.classList.toggle('show-menu');
            // Aggiunge/rimuove la classe per l'animazione dell'icona
            navToggle.classList.toggle('active'); 
        });
    }

    // Funzione per aggiornare la UI della navbar
    updateNavbar();

    // ========= NUOVA LOGICA PER MOSTRA/NASCONDI PASSWORD =========
    
    // Definiamo le icone SVG come stringhe per non dover aggiungere file
    const eyeIconSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-eye-fill" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/></svg>`;
    const eyeSlashIconSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-eye-slash-fill" viewBox="0 0 16 16"><path d="m10.79 12.912-1.614-1.615a3.5 3.5 0 0 1-4.474-4.474l-2.06-2.06C.938 6.278 0 8 0 8s3 5.5 8 5.5a7.029 7.029 0 0 0 2.79-.588zM5.21 3.088A7.028 7.028 0 0 1 8 2.5c5 0 8 5.5 8 5.5s-.939 1.721-2.641 3.238l-2.062-2.062a3.5 3.5 0 0 0-4.474-4.474L5.21 3.089z"/><path d="M5.525 7.646a2.5 2.5 0 0 0 2.829 2.829l-2.83-2.829zm4.95.708-2.829-2.83a2.5 2.5 0 0 1 2.829 2.829zm3.171 6-12-12 .708-.708 12 12-.708.708z"/></svg>`;

    // Seleziona TUTTE le icone per password presenti nella pagina
    const passwordToggles = document.querySelectorAll('.password-toggle-icon');

    passwordToggles.forEach(toggle => {
        // Imposta l'icona iniziale
        toggle.innerHTML = eyeIconSVG;

        toggle.addEventListener('click', () => {
            // Trova l'input password che precede immediatamente l'icona
            const passwordInput = toggle.previousElementSibling;

            if (passwordInput && passwordInput.tagName === 'INPUT') {
                // Controlla il tipo attuale e cambialo
                const isPassword = passwordInput.getAttribute('type') === 'password';
                passwordInput.setAttribute('type', isPassword ? 'text' : 'password');

                // Cambia l'icona in base al nuovo stato
                toggle.innerHTML = isPassword ? eyeSlashIconSVG : eyeIconSVG;
            }
        });
    });

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
 * Typing Indicator per Chat - Sistema di animazione puntini
 * =================================================================================
 */
const TypingIndicator = {
    /**
     * Crea e mostra l'indicatore di digitazione
     */
    show: function() {
        // Controlla se l'indicatore esiste già
        if (document.getElementById('typing-indicator')) return;
        
        // Crea l'elemento indicatore
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'typing-indicator';
        
        const dotsDiv = document.createElement('div');
        dotsDiv.className = 'typing-dots';
        
        // Crea i tre puntini animati
        for (let i = 0; i < 3; i++) {
            const span = document.createElement('span');
            dotsDiv.appendChild(span);
        }
        
        typingDiv.appendChild(dotsDiv);
        
        // Aggiunge l'indicatore alla chat window
        const chatWindow = document.getElementById('chat-window');
        if (chatWindow) {
            chatWindow.appendChild(typingDiv);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    },
    
    /**
     * Nasconde e rimuove l'indicatore di digitazione
     */
    hide: function() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
};

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
 * in base allo stato di login e al ruolo dell'utente.
 */
function updateNavbar() {
    const token = getAuthToken();
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

    // Link "I Nostri Medici": nascosto nella homepage, visibile altrove (tranne per i medici)
    const isHomepage = window.location.pathname === '/';
    const isMedico = userType === 'medico';
    const shouldHideCercaMedici = isHomepage || isMedico;
    navItems.cercaMedici?.classList.toggle('hidden', shouldHideCercaMedici);

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
 * Funzione helper per ottenere il token di autenticazione.
 * @returns {string|null} - Il token JWT o null se non presente.
 */
function getAuthToken() {
    return localStorage.getItem('user_token');
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
 * @param {boolean} isLoginRequest - Indica se questa è una richiesta di login (default: false).
 * @returns {Promise<object>} - I dati JSON della risposta.
 */
async function callApi(endpoint, options = {}, isLoginRequest = false) {
    const token = getAuthToken();
    
    const headers = options.headers || {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Aggiungi automaticamente Content-Type per richieste con body JSON
    if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }
    
    options.headers = headers;

    const response = await fetch(endpoint, options);

    if (response.status === 401) {
        if (isLoginRequest) {
            // Per richieste di login, l'errore 401 indica credenziali errate
            throw new Error('Email o password errati.');
        } else {
            // Per altre richieste, l'errore 401 indica sessione scaduta
            logout();
            throw new Error('Sessione scaduta. Effettua nuovamente il login.');
        }
    }
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `Errore HTTP: ${response.status}` }));
        const errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail) || `Errore HTTP: ${response.status}`;
        throw new Error(errorMessage);
    }

    return response.status === 204 ? {} : response.json();
}

/**
 * Escape HTML per prevenire XSS quando si inietta testo in innerHTML.
 */
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Sanifica numeri di telefono per link tel:
 * mantiene solo cifre e + iniziale.
 */
function sanitizePhone(str) {
    if (!str) return '';
    const s = String(str);
    const hasPlus = s.trim().startsWith('+');
    const digits = s.replace(/\D/g, '');
    return (hasPlus ? '+' : '') + digits;
}

/**
 * =================================================================================
 * Prenotazioni - Azioni comuni
 * =================================================================================
 */

async function handleCancelClick(prenotazioneId) {
    const userConfirmed = await SalusNotifier.confirm(
        "Sei sicuro di voler cancellare questa prenotazione? L'azione è irreversibile.",
        "Conferma Cancellazione"
    );
    if (!userConfirmed) return;
    try {
        await callApi(`/api/prenotazioni/${prenotazioneId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stato: 'Cancellata' })
        });
        SalusNotifier.alert('Prenotazione cancellata con successo!', 'Operazione Completata');
        setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
        SalusNotifier.alert(`Errore: ${error.message}`, 'Errore');
    }
}

async function handleCompleteClick(prenotazioneId) {
    const userConfirmed = await SalusNotifier.confirm(
        "Vuoi davvero segnare questa visita come completata?",
        "Conferma Azione"
    );
    if (!userConfirmed) return;
    try {
        await callApi(`/api/prenotazioni/${prenotazioneId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stato: 'Completata' })
        });
        SalusNotifier.alert('Visita segnata come completata!', 'Successo');
        setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
        SalusNotifier.alert(`Errore: ${error.message}`, 'Errore');
    }
}

/**
 * =================================================================================
 * Address Autocomplete Centralized System
 * =================================================================================
 * Sistema centralizzato per l'autocomplete degli indirizzi riutilizzabile in più template.
 */

/**
 * Initializza un sistema di autocomplete per indirizzi su un input specifico.
 * @param {string} inputId - ID dell'elemento input per la ricerca
 * @param {string} suggestionsContainerId - ID del container per i suggerimenti  
 * @param {function} onSuggestionSelect - Callback chiamato quando si seleziona un suggerimento
 * @param {number} minLength - Lunghezza minima per iniziare la ricerca (default: 3)
 * @param {number} debounceMs - Millisecondi di debounce (default: 300)
 * @param {function} customRenderer - Funzione personalizzata per rendering (opzionale)
 */
function initAddressAutocomplete(inputId, suggestionsContainerId, onSuggestionSelect, minLength = 3, debounceMs = 300, customRenderer = null) {
    const input = document.getElementById(inputId);
    const suggestionsContainer = document.getElementById(suggestionsContainerId);
    let debounceTimer;

    if (!input || !suggestionsContainer) {
        console.error(`initAddressAutocomplete: elementi non trovati - input: ${inputId}, suggestions: ${suggestionsContainerId}`);
        return;
    }

    // Mostra "Vicino a me" al focus se disponibile
    input.addEventListener('focus', function() {
        if (customRenderer && window.userLocation) {
            // Mostra solo "Vicino a me" quando il campo viene cliccato/focussato
            showAddressSuggestions([], suggestionsContainer, input, onSuggestionSelect, customRenderer);
        }
    });

    input.addEventListener('input', function() {
        const query = this.value.trim();
        clearTimeout(debounceTimer);
        suggestionsContainer.innerHTML = '';

        if (query.length < minLength) {
            // Se ha meno caratteri del minimo ma il customRenderer esiste, mostra almeno "Vicino a me"
            if (customRenderer && window.userLocation) {
                showAddressSuggestions([], suggestionsContainer, input, onSuggestionSelect, customRenderer);
            }
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/api/autocomplete-address?query=${encodeURIComponent(query)}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const suggestions = await response.json();
                showAddressSuggestions(suggestions, suggestionsContainer, input, onSuggestionSelect, customRenderer);
            } catch (error) {
                console.error('Errore autocomplete indirizzi:', error);
            }
        }, debounceMs);
    });

    // Nascondi suggerimenti quando si clicca fuori
    document.addEventListener('click', (e) => {
        if (e.target !== input) {
            suggestionsContainer.innerHTML = '';
        }
    });
}

/**
 * Mostra i suggerimenti di indirizzi nel container specificato
 * @param {Array} suggestions - Array di suggerimenti dall'API
 * @param {HTMLElement} container - Container dove mostrare i suggerimenti
 * @param {HTMLElement} input - Input element per aggiornare il valore
 * @param {function} onSelect - Callback per selezione suggerimento
 * @param {function} customRenderer - Funzione personalizzata per il rendering (opzionale)
 */
function showAddressSuggestions(suggestions, container, input, onSelect, customRenderer) {
    container.innerHTML = '';
    
    if (customRenderer && typeof customRenderer === 'function') {
        // Usa renderer personalizzato se fornito
        customRenderer(suggestions, container, input, onSelect);
        return;
    }
    
    // Renderer di default
    suggestions.forEach(suggestion => {
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = 'autocomplete-suggestion';
        suggestionDiv.textContent = suggestion.display_address || suggestion.nome || suggestion;
        
        suggestionDiv.addEventListener('click', function() {
            input.value = suggestion.display_address || suggestion.nome || suggestion;
            container.innerHTML = '';
            
            if (onSelect && typeof onSelect === 'function') {
                onSelect(suggestion);
            }
        });
        
        container.appendChild(suggestionDiv);
    });
}

/**
 * =================================================================================
 * Chat Helpers - funzioni riusabili per UI chat
 * =================================================================================
 */
const ChatHelpers = {
    detectSpecialistRecommendation(text) {
        const lowerText = String(text || '').toLowerCase();
        const triggers = [
            'allergologia','allergologo','andrologia','andrologo','angiologia','angiologo','audioprotesista',
            'cardiochirurgia','cardiochirurgo','cardiologia','cardiologo','chirurgia generale','chirurgo generale',
            'chirurgia maxillo-facciale','chirurgo maxillo-facciale','chirurgia plastica','chirurgo plastico','chirurgia estetica',
            'chirurgia toracica','chirurgo toracico','chirurgia vascolare','chirurgo vascolare',
            'dermatologia','dermatologo','venerologia','diabetologia','diabetologo',
            'dietologia','dietologo','nutrizionista','nutrizione','ematologia','ematologo',
            'endocrinologia','endocrinologo','epatologia','epatologo','fisiatria','fisiatra',
            'fisioterapia','fisioterapista','massofisioterapia','gastroenterologia','gastroenterologo',
            'geriatria','geriatra','ginecologia','ginecologo','immunologia','immunologo',
            'infettivologia','infettivologo','logopedia','logopedista','medicina dello sport','medico dello sport',
            'medicina legale','medico legale','medico di medicina generale','medicina generale','medico di base',
            'nefrologia','nefrologo','neurochirurgia','neurochirurgo','neurologia','neurologo',
            'odontoiatria','odontoiatra','dentista','ortodonzia','oftalmologia','oculistica','oculista',
            'oncologia','oncologo','ortopedia','ortopedico','osteopatia','osteopata',
            'otorinolaringoiatria','otorino','pediatria','pediatra','pneumologia','pneumologo',
            'podologia','podologo','psichiatria','psichiatra','radiologia','radiologo',
            'reumatologia','reumatologo','urologia','urologo'
        ];
        return triggers.some(t => lowerText.includes(t));
    },

    extractSpecialistInfo(text, allSpecializations) {
        if (!Array.isArray(allSpecializations) || allSpecializations.length === 0) return null;
        const lowerText = String(text || '').toLowerCase();
        const mapping = {
            'allergologo': 'Allergologia','andrologo': 'Andrologia','angiologo': 'Angiologia',
            'cardiochirurgo': 'Cardiochirurgia','cardiologo': 'Cardiologia','chirurgo generale': 'Chirurgia Generale',
            'chirurgo maxillo-facciale': 'Chirurgia Maxillo-Facciale','chirurgo plastico': 'Chirurgia Plastica ed Estetica','chirurgia estetica': 'Chirurgia Plastica ed Estetica',
            'chirurgo toracico': 'Chirurgia Toracica','chirurgo vascolare': 'Chirurgia Vascolare',
            'dermatologo': 'Dermatologia e Venerologia','venerologia': 'Dermatologia e Venerologia','diabetologo': 'Diabetologia',
            'dietologo': 'Dietologia e Nutrizione','nutrizionista': 'Dietologia e Nutrizione','ematologo': 'Ematologia',
            'endocrinologo': 'Endocrinologia','epatologo': 'Epatologia','fisiatra': 'Fisiatria',
            'fisioterapista': 'Fisioterapia e Massofisioterapia','gastroenterologo': 'Gastroenterologia',
            'geriatra': 'Geriatria','ginecologo': 'Ginecologia','immunologo': 'Immunologia',
            'infettivologo': 'Infettivologia','logopedista': 'Logopedia','medico dello sport': 'Medicina dello Sport',
            'medico legale': 'Medicina Legale','medicina generale': 'Medico di Medicina Generale','medico di base': 'Medico di Medicina Generale',
            'nefrologo': 'Nefrologia','neurochirurgo': 'Neurochirurgia','neurologo': 'Neurologia',
            'odontoiatra': 'Odontoiatria e Ortodonzia','dentista': 'Odontoiatria e Ortodonzia','ortodonzia': 'Odontoiatria e Ortodonzia',
            'oftalmologo': 'Oftalmologia (Oculistica)','oculista': 'Oftalmologia (Oculistica)','oncologo': 'Oncologia',
            'ortopedico': 'Ortopedia','osteopata': 'Osteopatia','otorino': 'Otorinolaringoiatria',
            'pediatra': 'Pediatria','pneumologo': 'Pneumologia','podologo': 'Podologia',
            'psichiatra': 'Psichiatria','radiologo': 'Radiologia e Radiologia Diagnostica',
            'reumatologo': 'Reumatologia','urologo': 'Urologia'
        };
        for (const spec of allSpecializations) {
            if (lowerText.includes((spec.nome || '').toLowerCase())) return { id: spec.id, name: spec.nome };
        }
        for (const [variation, fullName] of Object.entries(mapping)) {
            if (lowerText.includes(variation)) {
                const spec = allSpecializations.find(s => s.nome === fullName);
                if (spec) return { id: spec.id, name: spec.nome };
            }
        }
        return null;
    },

    disableChatInput(chatInput, submitBtn, resetBtn) {
        if (chatInput) {
            chatInput.disabled = true;
            chatInput.placeholder = "Clicca 'Prenota ora!' o inizia una nuova conversazione";
        }
        if (submitBtn) submitBtn.disabled = true;
        if (resetBtn) resetBtn.style.display = 'block';
    },

    enableChatInput(chatInput, submitBtn) {
        if (chatInput) {
            chatInput.disabled = false;
            chatInput.placeholder = "Es. 'Ho un forte mal di schiena da alcuni giorni...'";
            chatInput.focus();
        }
        if (submitBtn) submitBtn.disabled = false;
    },

    createBookingButton(specialistInfo, onClick) {
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'specialist-booking-container';
        const bookingButton = document.createElement('button');
        bookingButton.className = 'quick-action-btn specialist-booking-btn';
        bookingButton.textContent = '🩺 Prenota ora!';
        if (typeof onClick === 'function') bookingButton.addEventListener('click', onClick);
        buttonContainer.appendChild(bookingButton);
        return buttonContainer;
    },

    handleBookingRedirect(specialistInfo, userLocation) {
        const params = new URLSearchParams();
        params.append('specializzazione_id', specialistInfo.id);
        if (userLocation && userLocation.lat && userLocation.lon) {
            params.append('lat', userLocation.lat);
            params.append('lon', userLocation.lon);
        }
        window.location.href = `/medici?${params.toString()}`;
    }
};

/**
 * API client per le chiamate chat (backend LangGraph).
 */
const ChatAPI = {
    async sendMessage(sessionId, userMessage) {
        // Validazione input
        if (!sessionId || typeof sessionId !== 'string') {
            throw new Error('Session ID non valido');
        }
        if (!userMessage || typeof userMessage !== 'string' || userMessage.trim() === '') {
            throw new Error('Messaggio non valido');
        }

        const token = getAuthToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        const response = await fetch('/chat/message', {
            method: 'POST',
            headers,
            body: JSON.stringify({ 
                session_id: sessionId, 
                messages: [{ role: 'user', content: userMessage.trim() }] 
            })
        });
        
        if (response.status === 422) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Validation error 422:', errorData);
            throw new Error('Dati di input non validi. Riprova con un messaggio diverso.');
        }
        if (!response.ok) {
            throw new Error(`Errore dal server: ${response.statusText}`);
        }
        return response.json();
    },

    async resetSession(sessionId) {
        const token = getAuthToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const response = await fetch('/chat/reset', {
            method: 'POST',
            headers,
            body: JSON.stringify({ session_id: sessionId, messages: [] })
        });
        return response.ok;
    }
};

/**
 * UI helpers per la chat
 */
const ChatUI = {
    appendMessage(chatWindow, text, role, allSpecializations, userLocation, chatInput, resetBtn) {
        const messageContainer = document.createElement('div');
        messageContainer.className = `chat-message ${role}-message`;
        const messageParagraph = document.createElement('p');
        messageParagraph.textContent = text;
        messageContainer.appendChild(messageParagraph);
        chatWindow.appendChild(messageContainer);
        const submitBtn = document.getElementById('chat-submit-btn');
        if (role === 'assistant' && ChatHelpers.detectSpecialistRecommendation(text)) {
            const specialistInfo = ChatHelpers.extractSpecialistInfo(text, allSpecializations);
            if (specialistInfo) {
                const bookingButton = ChatHelpers.createBookingButton(specialistInfo, () => ChatHelpers.handleBookingRedirect(specialistInfo, userLocation));
                chatWindow.appendChild(bookingButton);
                ChatHelpers.disableChatInput(chatInput, submitBtn, resetBtn);
            }
        }
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
};

/**
 * Autocomplete semplice basato su array in memoria.
 * getItems: funzione che restituisce l'array corrente (es. allSpecializations)
 * itemTextFn: funzione che estrae il testo da mostrare (es. spec => spec.nome)
 */
function initSimpleAutocomplete(inputId, suggestionsContainerId, getItems, onSelect, itemTextFn, minLength = 0, debounceMs = 300) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(suggestionsContainerId);
    let debounceTimer;

    if (!input || !container) return;

    function render(suggestions) {
        container.innerHTML = '';
        const items = suggestions.slice(0, 8);
        items.forEach(item => {
            const div = document.createElement('div');
            div.textContent = itemTextFn(item);
            div.addEventListener('click', () => {
                input.value = itemTextFn(item);
                container.innerHTML = '';
                if (onSelect) onSelect(item);
            });
            container.appendChild(div);
        });
        if (suggestions.length > 8) {
            const showAllDiv = document.createElement('div');
            showAllDiv.textContent = `Visualizza tutte (${suggestions.length})`;
            showAllDiv.className = 'show-all-option';
            showAllDiv.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                container.innerHTML = '';
                container.classList.add('show-all-active');
                suggestions.forEach(item => {
                    const div = document.createElement('div');
                    div.textContent = itemTextFn(item);
                    div.addEventListener('click', () => {
                        input.value = itemTextFn(item);
                        container.innerHTML = '';
                        container.classList.remove('show-all-active');
                        if (onSelect) onSelect(item);
                    });
                    container.appendChild(div);
                });
            });
            container.appendChild(showAllDiv);
        }
    }

    input.addEventListener('focus', () => {
        const items = getItems() || [];
        if (items.length) render(items);
    });

    input.addEventListener('input', () => {
        const q = input.value.trim().toLowerCase();
        clearTimeout(debounceTimer);
        if (q.length < minLength) {
            container.innerHTML = '';
            return;
        }
        debounceTimer = setTimeout(() => {
            const items = (getItems() || []).filter(it => itemTextFn(it).toLowerCase().includes(q));
            render(items);
        }, debounceMs);
    });

    document.addEventListener('click', (e) => {
        if (e.target !== input) container.innerHTML = '';
    });
}
