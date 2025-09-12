"""
Intent Classifier - Classificazione Intent per Medical Triage Chatbot

Sistema di classificazione intent per distinguere tra diversi tipi di richieste utente:
- greeting: Saluti e domande generiche
- symptom_description: Descrizioni mediche effettive  
- emergency: Situazioni di emergenza
- out_of_scope: Richieste fuori contesto

Ottimizzato per progetto universitario: semplice, funzionale e ben documentato.
"""

import logging
from typing import Literal
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage
from .config import LLM_MODEL, OLLAMA_BASE_URL
from pydantic import BaseModel, Field

# Tipi di intent supportati
IntentType = Literal["greeting", "symptom_description", "emergency", "out_of_scope"]

class IntentClassification(BaseModel):
    """Schema per classificazione intent"""
    intent: IntentType = Field(description="Categoria di intent rilevata")
    confidence: float = Field(ge=0, le=100, description="Confidenza della classificazione (0-100)")
    reasoning: str = Field(description="Breve spiegazione della classificazione")

    

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Classificatore intent per triage medico"""
    
    def __init__(self):
        self.llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0  # Deterministic per consistency
        )
        
        self.classification_prompt = ChatPromptTemplate.from_template("""
Sei un classificatore AI per un assistente sanitario virtuale che analizza conversazioni mediche.

Analizza l'INTERA CRONOLOGIA della conversazione per classificare l'INTENT dell'ultimo messaggio utente in una di queste 4 categorie:

1. **greeting**: Saluti iniziali, presentazioni, domande generiche sul servizio
   Esempi: "Ciao", "Buongiorno", "Puoi aiutarmi?", "Come funzioni?", "Non so a quale specialista rivolgermi"

2. **symptom_description**: Descrizioni di sintomi, disturbi medici, INCLUSE risposte a domande di follow-up mediche
   Esempi: "Ho mal di testa", "Dolore al petto da ieri", "Febbre alta"
   FOLLOW-UP: "Da ieri", "Sì", "No", "Un po'" (quando rispondono a domande mediche del bot)

3. **emergency**: Situazioni di emergenza che richiedono intervento immediato
   Esempi: "Non riesco a respirare", "Dolore fortissimo al petto", "Perdita di coscienza", "Emorragia grave",
   "trauma cranico con perdita di coscienza o vomito", "sospetta frattura esposta", "politrauma",
   "dolore cervicale importante dopo incidente con formicolii o debolezza"

4. **out_of_scope**: Richieste completamente fuori dal contesto sanitario
   Esempi: "Che tempo fa?", "Dove comprare scarpe?", "Ricetta pasta", "Sport di oggi"

CRONOLOGIA CONVERSAZIONE COMPLETA:
{conversation_history}

ULTIMO MESSAGGIO UTENTE DA CLASSIFICARE:
{user_message}

ISTRUZIONI CONTEXT-AWARE:
- Se il bot ha appena fatto una domanda medica (es. "Da quanto tempo?", "Hai altri sintomi?"), 
  la risposta utente è molto probabilmente **symptom_description**, anche se breve o ambigua
- Se l'utente risponde "Da ieri", "Sì", "No", "Un po'" dopo una domanda del bot sui sintomi → symptom_description
- Se è il primo messaggio o non c'è contesto medico precedente, usa classificazione standard
- emergency SOLO per situazioni veramente urgenti che richiedono 118 (inclusi traumi gravi con segnali d'allarme, es. perdita di coscienza post-trauma, frattura esposta)
- Considera il FLUSSO CONVERSAZIONALE per determinare l'intent corretto

ESEMPI CONTEXT-AWARE:
Bot: "Da quanto tempo hai questo mal di testa?"
User: "Da ieri" → symptom_description (follow-up, NON out_of_scope)

Bot: "Hai altri sintomi insieme al mal di testa?"  
User: "No" → symptom_description (risposta medica, NON greeting)

User: "Che tempo fa?" (primo messaggio) → out_of_scope

Fornisci la classificazione con confidenza (0-100) e una breve spiegazione del ragionamento.
        """)
        
        # Nota: logiche di interrupt rimosse perché non utilizzate attualmente
    
    async def classify_intent(self, user_message: str) -> IntentClassification:
        """
        Classifica l'intent del messaggio utente.
        
        Args:
            user_message: Messaggio dell'utente da classificare
            
        Returns:
            IntentClassification: Classificazione strutturata con confidence e reasoning
        """
        try:
            # Structured LLM per output affidabile
            structured_llm = self.llm.with_structured_output(IntentClassification)
            classification_chain = self.classification_prompt | structured_llm
            
            logger.debug(f"Classifying intent for message: {user_message[:50]}...")
            
            result = await classification_chain.ainvoke({
                "user_message": user_message
            })
            
            logger.info(f"Intent classified: {result.intent} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            # Fallback conservativo: tratta come greeting per sicurezza
            return IntentClassification(
                intent="greeting",
                confidence=0,
                reasoning="Errore nella classificazione - fallback a greeting per sicurezza"
            )
    
    async def classify_from_messages(self, messages: list[BaseMessage]) -> IntentClassification:
        """
        Classifica intent basandosi sull'intera cronologia conversazionale (context-aware).
        
        Args:
            messages: Lista messaggi completa della conversazione
            
        Returns:
            IntentClassification: Classificazione context-aware dell'ultimo messaggio utente
        """
        # Estrai ultimo messaggio utente
        last_user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_message = msg.content
                break
        
        if not last_user_message:
            logger.warning("No user message found in conversation history")
            return IntentClassification(
                intent="greeting",
                confidence=50,
                reasoning="Nessun messaggio utente trovato - default a greeting"
            )
        
        # Costruisci cronologia formattata per context-awareness
        conversation_history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation_history.append(f"Utente: {msg.content}")
            elif hasattr(msg, 'content') and msg.content:  # AIMessage
                # Aggiungi solo messaggi bot non vuoti
                conversation_history.append(f"Bot: {msg.content}")
        
        history_text = "\n".join(conversation_history) if conversation_history else "(Nessuna cronologia)"
        
        # Classifica con context awareness
        try:
            structured_llm = self.llm.with_structured_output(IntentClassification)
            classification_chain = self.classification_prompt | structured_llm
            
            logger.debug(f"Context-aware classification for: {last_user_message[:50]}... (history: {len(conversation_history)} messages)")
            
            result = await classification_chain.ainvoke({
                "conversation_history": history_text,
                "user_message": last_user_message
            })
            
            logger.info(f"Context-aware intent: {result.intent} (confidence: {result.confidence}) - {result.reasoning}")
            return result
            
        except Exception as e:
            logger.error(f"Error in context-aware classification: {e}")
            # Fallback: usa classificazione base senza contesto
            return await self.classify_intent(last_user_message)
    
    

# Istanza globale per uso nei nodi LangGraph
intent_classifier = IntentClassifier()
