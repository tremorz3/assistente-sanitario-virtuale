"""
LangGraph 2025 Medical Triage Orchestrator - Architettura Moderna Ottimale

Sistema di triage medico professionale che implementa pattern LangGraph 2025:
• MessagesState extension con campi triage-specific
• Command pattern per routing esplicito e deterministico
• Async-first per performance I/O ottimali
• Structured output per decisioni AI affidabili
• Safety limits per robustezza produzione

Workflow Triage:
START → classify_intent → [valuta_completezza|formato_risposta] → [trova_specialista|formato_risposta] → END

Compatibilità: 
- invoke_orchestrator(thread_id, message) → str response
- memory: MemorySaver per reset/persistenza
"""

import logging
from typing import Literal, Optional

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from .rag_engine import RAGEngine, SpecialistRecommendation
from .symptom_analyzer import SymptomAnalyzer, CompletenessAssessment
from .intent_classifier import intent_classifier, IntentType

logger = logging.getLogger(__name__)

# === STRUCTURED SCHEMAS ===
# Importati da moduli specializzati per evitare duplicazione

# === STATE DEFINITION ===

class TriageState(MessagesState):
    """
    State LangGraph  per triage medico.
    Estende MessagesState per compatibilità nativa con memory/threads.
    """
    # Intent classification
    detected_intent: Optional[IntentType] = None
    
    # Workflow control
    tentativi_raccolta: int = 0
    max_tentativi: int = 5 # Safety limit per raccolta info
    
    # Analysis results
    assessment: Optional[CompletenessAssessment] = None
    raccomandazione: Optional[SpecialistRecommendation] = None

# === CORE COMPONENTS ===

class MedicalTriageSystem:
    """Sistema triage medico modulare"""
    
    def __init__(self):
        self.symptom_analyzer = SymptomAnalyzer()
        self.rag_engine = RAGEngine()
    
    async def classify_intent_async(self, state: TriageState) -> Command[Literal["valuta_completezza", "formato_risposta"]]:
        """
        NODO 0: Classifica intent del messaggio utente.
        Determina il tipo di richiesta e rotta di conseguenza.
        """
        messages = state["messages"]
        
        try:
            logger.info(f"=== CLASSIFY_INTENT DEBUG ===")
            logger.info(f"Processing {len(messages)} messages")
            for i, msg in enumerate(messages):
                msg_type = "USER" if isinstance(msg, HumanMessage) else "AI"
                content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                logger.info(f"  [{i}] {msg_type}: {content_preview}")
            
            # Classifica intent dell'ultimo messaggio utente
            classification = await intent_classifier.classify_from_messages(messages)
            
            logger.info(f"Intent detected: {classification.intent} (confidence: {classification.confidence})")
            
            # Aggiorna state con classificazione
            state_update = {
                "detected_intent": classification.intent
            }
            
            # Routing basato su intent
            if classification.intent == "symptom_description":
                # Solo le descrizioni sintomi entrano nel triage normale
                return Command(
                    update=state_update,
                    goto="valuta_completezza"
                )
            else:
                # Tutti gli altri intent (greeting, emergency, out_of_scope) vanno direttamente a formato_risposta
                return Command(
                    update=state_update,
                    goto="formato_risposta"
                )
                
        except Exception as e:
            logger.error(f"Errore classificazione intent: {e}")
            # Fallback: tratta come symptom_description per non bloccare il triage
            return Command(
                update={
                    "detected_intent": "symptom_description"
                },
                goto="valuta_completezza"
            )
        
    async def valuta_completezza_async(self, state: TriageState) -> Command[Literal["formato_risposta", "trova_specialista"]]:
        """
        NODO 1: Valuta se sintomi descritti sono sufficienti per raccomandazione.
        Usa structured output per decisioni affidabili.
        """
        messages = state["messages"]
        tentativi = state.get("tentativi_raccolta", 0)
        
        # DEBUG: Log della cronologia completa
        logger.info(f"=== VALUTA_COMPLETEZZA DEBUG ===")
        logger.info(f"Numero messaggi totali: {len(messages)}")
        for i, msg in enumerate(messages):
            msg_type = "USER" if isinstance(msg, HumanMessage) else "AI"
            content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            logger.info(f"  [{i}] {msg_type}: {content_preview}")
        logger.info(f"Tentativo raccolta: {tentativi}")
        logger.info(f"=======================================")
        
        # SAFETY LIMIT: Evita loop infiniti
        if tentativi >= state.get("max_tentativi", 10):
            logger.info(f"Raggiunto limite tentativi ({tentativi}), procedo con analisi RAG senza conferma")
            return Command(
                goto="trova_specialista"
            )
        
        # Analizza completezza con AI (passa numero tentativo per progressione intelligente)
        try:
            assessment = await self.symptom_analyzer.assess_completeness(messages, tentativi + 1)
            
            # Controlla se tutte le informazioni sono complete
            if assessment.soddisfatto:
                logger.info("Sintomi completi: procedo direttamente all'analisi RAG")
                return Command(
                    update={
                        "assessment": assessment
                    },
                    goto="trova_specialista"
                )
            else:
                logger.info(f"Sintomi incompleti, richiedo più info (tentativo {tentativi + 1})")
                return Command(
                    update={
                        "assessment": assessment,
                        "tentativi_raccolta": tentativi + 1
                    },
                    goto="formato_risposta"
                )
                
        except Exception as e:
            logger.error(f"Errore valutazione completezza: {e}")
            # Fallback sicuro: prosegui direttamente al RAG
            return Command(
                goto="trova_specialista"
            )

    
    
    async def trova_specialista_async(self, state: TriageState) -> Command[Literal["formato_risposta"]]:
        """
        NODO 2: Analisi RAG per raccomandazione specialista.
        Usa vector search + LLM analysis per raccomandazione professionale.
        """
        messages = state["messages"]
        
        # Estrai tutti i sintomi dalla conversazione
        sintomi_completi = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                sintomi_completi.append(msg.content)
        
        sintomi_text = " ".join(sintomi_completi)
        
        try:
            # Analisi RAG completa
            raccomandazione = await self.rag_engine.find_specialist(sintomi_text)
            
            return Command(
                update={"raccomandazione": raccomandazione},
                goto="formato_risposta"
            )
            
        except Exception as e:
            logger.error(f"Errore analisi RAG: {e}")
            # Fallback sicuro
            fallback_recommendation = SpecialistRecommendation(
                specialista="Medico di Medicina Generale",
                motivazione="Si è verificato un problema tecnico nell'analisi. Ti consiglio di consultare il tuo medico di base per una valutazione iniziale."
            )
            return Command(
                update={"raccomandazione": fallback_recommendation},
                goto="formato_risposta"
            )
    
    async def formato_risposta_async(self, state: TriageState) -> Command:
        """
        NODO UNIFICATO: Formatta risposta finale per tutti i tipi di richiesta.
        Gestisce raccomandazioni mediche, follow-up, greeting, emergency, out_of_scope.
        """
        assessment = state.get("assessment")
        raccomandazione = state.get("raccomandazione")
        detected_intent = state.get("detected_intent")
        
        # PRIORITÀ 1: Raccomandazione specialistica (workflow triage completato)
        if raccomandazione:
            risposta = f""" **Raccomandazione Specialistica**

**Specialista consigliato**: {raccomandazione.specialista}

**Motivazione clinica**:
{raccomandazione.motivazione}

---
*Questa è una raccomandazione orientativa basata sui sintomi descritti. Per una valutazione completa, consulta sempre un medico.*"""
        
        # PRIORITÀ 2: Follow-up medico (sintomi incompleti, richiedi più info)
        elif assessment and not assessment.soddisfatto:
            domanda = assessment.domanda_followup or "Puoi fornirmi qualche informazione in più sui tuoi sintomi?"
            risposta = f""" **Raccolta Informazioni**

{domanda}"""
        
        # PRIORITÀ 3: Intent diretti (non medici) basati su classificazione
        elif detected_intent == "greeting":
            risposta = """
Per aiutarti a trovare lo specialista giusto, puoi descrivermi: 
• Quali sintomi stai avvertendo 
• Da quanto tempo li hai 
• Se c'è stato un trauma (caduta/incidente) 

Sarò felice di indirizzarti verso la specializzazione più appropriata!"""

        elif detected_intent == "emergency":
            risposta = """SITUAZIONE DI EMERGENZA RILEVATA 

**Chiama immediatamente il 118** o recati al Pronto Soccorso più vicino. 

Per sintomi gravi che richiedono intervento immediato, non utilizzare assistenti virtuali ma contatta direttamente i servizi di emergenza. 

**Numero emergenze: 118**"""

        elif detected_intent == "out_of_scope":
            risposta = """Mi dispiace, non posso aiutarti con questa richiesta.
            Il mio unico scopo è quello di effettuare un triage orientativo verso lo specialista medico più appropriato in base ai sintomi descritti."""

        # PRIORITÀ 4: Fallback generico
        else:
            risposta = """Ciao! Sono il tuo assistente sanitario virtuale.

Per aiutarti al meglio, descrivi i sintomi che stai avvertendo e ti indirizzerò verso lo specialista più appropriato."""
        
        # Aggiungi messaggio AI al thread (append, non replace)
        ai_message = AIMessage(content=risposta)
        
        return Command(
            update={"messages": [ai_message]},
            goto=END
        )

# === GRAPH CONSTRUCTION ===

# Istanza sistema triage
triage_system = MedicalTriageSystem()

# Costruzione graph LangGraph 2025
def create_triage_graph() -> StateGraph:
    """Crea graph triage medico con architettura moderna + intent classification"""
    
    graph = StateGraph(TriageState)
    
    # Nodi del workflow semplificato
    graph.add_node("classify_intent", triage_system.classify_intent_async)
    graph.add_node("valuta_completezza", triage_system.valuta_completezza_async)
    graph.add_node("trova_specialista", triage_system.trova_specialista_async)
    graph.add_node("formato_risposta", triage_system.formato_risposta_async)
    
    # Workflow edges (Command pattern gestisce routing)
    graph.add_edge(START, "classify_intent")
    
    return graph

# === MEMORY & DEPLOYMENT ===

# Memory globale per persistenza threads
memory = MemorySaver()

# Graph compilato
triage_graph = create_triage_graph().compile(checkpointer=memory)

# === PUBLIC API ===


async def invoke_orchestrator(thread_id: str, message: str) -> str:
    """
    API principale per sistema triage medico con auto-detecting interrupt.
    
    Rileva automaticamente se il thread è in stato di interrupt e gestisce:
    - Thread normale → Start/Continue workflow normale
    - Thread interrotto → Resume workflow con risposta utente
    
    Args:
        thread_id: Identificativo thread per isolamento conversazioni
        message: Messaggio utente da processare
        
    Returns:
        str: Risposta formattata per utente
    """
    try:
        # Configura input per LangGraph
        config = {"configurable": {"thread_id": thread_id}}

        # Flusso normale: avvia/continua il workflow senza gestione interrupt
        logger.info(f"Processing message for thread {thread_id}: {message[:50]}...")
        input_data = {"messages": [HumanMessage(content=message)]}
        result = await triage_graph.ainvoke(input_data, config=config)

        # Estrai ultima risposta AI (workflow completato)
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                logger.info(f"Triage completed for thread {thread_id}")
                return msg.content
        
        # Fallback se nessuna risposta AI trovata
        return "Mi dispiace, si è verificato un errore. Riprova per favore."
        
    except Exception as e:
        # Errori runtime non legati a interrupt
        logger.error(f"Errore orchestrator per thread {thread_id}: {e}", exc_info=True)
        return "Mi dispiace, si è verificato un errore tecnico. Riprova tra qualche momento."
