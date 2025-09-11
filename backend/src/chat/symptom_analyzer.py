"""
SymptomAnalyzer - Analizzatore AI per Valutazione Completezza Sintomi

Modulo specializzato per valutare se le informazioni sui sintomi fornite
dall'utente sono sufficienti per una raccomandazione specialistica affidabile.

Usa structured output per decisioni deterministiche e domande follow-up intelligenti.
"""

import logging
from typing import List, Optional
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage
from .config import LLM_MODEL, OLLAMA_BASE_URL
from pydantic import BaseModel, Field

class CompletenessAssessment(BaseModel):
    """Schema per valutazione completezza sintomi"""
    sufficiente: bool = Field(description="True se info sufficienti per raccomandazione specialista")
    punteggio: int = Field(ge=0, le=100, description="Punteggio completezza (0-100, sufficiente ≥60)")
    confidenza: float = Field(ge=0, le=100, description="Confidenza valutazione (0-100)")
    domanda_followup: Optional[str] = Field(description="Domanda specifica per elemento mancante più critico")
    elementi_mancanti: list[str] = Field(description="Lista elementi mancanti in ordine di priorità")
    elemento_mancante_critico: Optional[str] = Field(description="Elemento singolo più importante da raccogliere")

logger = logging.getLogger(__name__)

class SymptomAnalyzer:
    """Analizzatore sintomi con AI per triage medico"""
    
    def __init__(self):
        self.llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0  # Deterministic per consistency
        )
        
        self.assessment_prompt = ChatPromptTemplate.from_template("""
Sei un assistente medico AI che valuta la completezza delle informazioni sui sintomi in modo progressivo e user-friendly.

Analizza TUTTI i messaggi dell'utente (non solo l'ultimo) per valutare le informazioni raccolte finora.

MESSAGGIO ATTUALE:
{current_message}

CRONOLOGIA CONVERSAZIONE COMPLETA:
{conversation_history}

TENTATIVO CORRENTE: {tentativo_numero}

SISTEMA DI PUNTEGGIO (sufficiente ≥60/100):
• Sintomo principale specifico: +35 punti
• Durata/frequenza chiara: +25 punti  
• Presenza/assenza di trauma: +20 punti
• Sintomi accessori significativi: +20 punti
• Caratteristiche del sintomo: +10 punti (opzionale)

ACCETTA LINGUAGGIO COMUNE:
✅ "Male da ieri" (durata implicita)
✅ "Dolore forte" (intensità come caratteristica)
✅ "Non riesco a dormire" (impatto funzionale)
✅ "Fa male tantissimo" (intensità implicita)
✅ "Sono caduto ieri" (trauma implicito)
✅ "Dopo la botta" (trauma implicito)

STRATEGIA DOMANDE SPECIFICHE PER ELEMENTO MANCANTE:
- Se manca SINTOMO_SPECIFICO: "Per aiutarti al meglio, puoi descrivermi che tipo di disturbo o fastidio stai avvertendo?"
- Se manca DURATA: "Da quanto tempo avverti questo [sintoma]? È iniziato oggi, ieri, qualche giorno fa?"
- Se manca TRAUMA: "Questo [sintoma] è comparso dopo una caduta, un colpo, un incidente o qualche trauma? Oppure è iniziato spontaneamente?"
- Se mancano SINTOMI_ACCESSORI: "Hai notato altri sintomi insieme a questo [sintoma]? Ad esempio nausea, febbre, sudorazione o altro?"
- Se manca CARATTERISTICHE: "Come descriveresti questo [sintoma]? È un dolore sordo, pulsante, bruciante, o di altro tipo?" (solo se necessario per completezza)

STRATEGIA PER TENTATIVO:
- Tentativo 1: Domanda su elemento_mancante_critico (il più importante)
- Tentativo 2: Domanda su secondo elemento dalla lista elementi_mancanti
- Tentativo 3: Domanda finale su dettaglio mancante + avviso che si procederà

IMPORTANTE: 
- Usa sempre il campo elemento_mancante_critico per generare domanda specifica
- Personalizza la domanda con il sintoma già menzionato se presente
- Genera domande conversazionali, empatiche e specifiche
- Evita gergo medico complesso
        """)
    
    async def assess_completeness(self, current_message: str, conversation_history: List[BaseMessage], tentativo_numero: int = 1) -> CompletenessAssessment:
        """
        Valuta completezza informazioni sintomi usando AI structured output progressivo.
        
        Args:
            current_message: Ultimo messaggio utente
            conversation_history: Cronologia messaggi precedenti
            tentativo_numero: Numero tentativo corrente (1-3)
            
        Returns:
            CompletenessAssessment: Valutazione strutturata con domande follow-up intelligenti
        """
        try:
            # Combina TUTTI i messaggi utente per analisi completa
            all_user_messages = []
            for msg in conversation_history:
                if isinstance(msg, HumanMessage):
                    all_user_messages.append(f"Utente: {msg.content}")
            
            # Aggiungi il messaggio corrente se non già incluso
            if current_message and f"Utente: {current_message}" not in all_user_messages:
                all_user_messages.append(f"Utente: {current_message}")
            
            history_text = "\n".join(all_user_messages) if all_user_messages else "(Nessuna cronologia precedente)"
            
            # Structured LLM per output affidabile
            structured_llm = self.llm.with_structured_output(CompletenessAssessment)
            assessment_chain = self.assessment_prompt | structured_llm
            
            logger.debug(f"Analyzing symptom completeness: {current_message[:50]}...")
            
            result = await assessment_chain.ainvoke({
                "current_message": current_message,
                "conversation_history": history_text,
                "tentativo_numero": tentativo_numero
            })
            
            logger.info(f"Completeness assessment: sufficient={result.sufficiente}, confidence={result.confidenza}")
            return result
            
        except Exception as e:
            logger.error(f"Error in symptom analysis: {e}")
            # Fallback conservativo: domanda specifica per primo contatto
            return CompletenessAssessment(
                sufficiente=False,
                punteggio=10,
                confidenza=0,
                domanda_followup="Per aiutarti al meglio, puoi descrivermi che tipo di disturbo o fastidio stai avvertendo?",
                elementi_mancanti=["sintomo_specifico", "durata", "trauma", "sintomi_accessori"],
                elemento_mancante_critico="sintomo_specifico"
            )
    
    def _extract_symptoms_from_history(self, history: List[BaseMessage]) -> str:
        """Estrae tutti i sintomi dalla cronologia conversazione"""
        symptoms = []
        for msg in history:
            if isinstance(msg, HumanMessage):
                symptoms.append(msg.content)
        return " | ".join(symptoms)