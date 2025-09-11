"""
LangGraph 2025 Medical Triage Orchestrator - Architettura Moderna Ottimale

Sistema di triage medico professionale che implementa pattern LangGraph 2025:
• MessagesState extension con campi triage-specific
• Command pattern per routing esplicito e deterministico
• Async-first per performance I/O ottimali
• Structured output per decisioni AI affidabili
• Safety limits per robustezza produzione

Workflow Triage:
START → valuta_completezza → trova_specialista → formato_risposta → END

Compatibilità: 
- invoke_orchestrator(thread_id, message) → str response
- memory: MemorySaver per reset/persistenza
"""

import asyncio
import logging
from typing import Literal, Optional, Dict, Any

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

from .config import LLM_MODEL, OLLAMA_BASE_URL
from .rag_engine import RAGEngine, SpecialistRecommendation
from .symptom_analyzer import SymptomAnalyzer, CompletenessAssessment

logger = logging.getLogger(__name__)

# === STRUCTURED SCHEMAS ===
# Importati da moduli specializzati per evitare duplicazione

# === STATE DEFINITION ===

class TriageState(MessagesState):
    """
    State LangGraph 2025 per triage medico.
    Estende MessagesState per compatibilità nativa con memory/threads.
    """
    # Workflow control
    completezza_valutata: bool = False
    tentativi_raccolta: int = 0
    max_tentativi: int = 3
    
    # Analysis results
    assessment: Optional[CompletenessAssessment] = None
    raccomandazione: Optional[SpecialistRecommendation] = None

# === CORE COMPONENTS ===

class MedicalTriageSystem:
    """Sistema triage medico modulare"""
    
    def __init__(self):
        self.symptom_analyzer = SymptomAnalyzer()
        self.rag_engine = RAGEngine()
        
    async def valuta_completezza_async(self, state: TriageState) -> Command[Literal["valuta_completezza", "trova_specialista", "formato_risposta"]]:
        """
        NODO 1: Valuta se sintomi descritti sono sufficienti per raccomandazione.
        Usa structured output per decisioni affidabili.
        """
        messages = state["messages"]
        tentativi = state.get("tentativi_raccolta", 0)
        
        # SAFETY LIMIT: Evita loop infiniti
        if tentativi >= state.get("max_tentativi", 3):
            logger.info(f"Raggiunto limite tentativi ({tentativi}), procedo con analisi")
            return Command(
                update={"completezza_valutata": True},
                goto="trova_specialista"
            )
        
        # Estrai ultimo messaggio utente
        ultimo_messaggio = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                ultimo_messaggio = msg.content
                break
        
        if not ultimo_messaggio:
            # Usa AI anche per primo messaggio vuoto per generare domanda appropriata
            ultimo_messaggio = "Ciao"  # Messaggio minimo per far funzionare l'AI
        
        # Analizza completezza con AI (passa numero tentativo per progressione intelligente)
        try:
            assessment = await self.symptom_analyzer.assess_completeness(ultimo_messaggio, messages, tentativi + 1)
            
            if assessment.sufficiente:
                logger.info("Sintomi sufficienti per analisi RAG")
                return Command(
                    update={
                        "assessment": assessment,
                        "completezza_valutata": True
                    },
                    goto="trova_specialista"
                )
            else:
                logger.info(f"Sintomi insufficienti, richiedo più info (tentativo {tentativi + 1})")
                return Command(
                    update={
                        "assessment": assessment,
                        "tentativi_raccolta": tentativi + 1
                    },
                    goto="formato_risposta"
                )
                
        except Exception as e:
            logger.error(f"Errore valutazione completezza: {e}")
            # Fallback: procedi con analisi se valutazione fallisce
            return Command(
                update={"completezza_valutata": True},
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
    
    async def formato_risposta_async(self, state: TriageState) -> Command[Literal[END]]:
        """
        NODO 3: Formatta risposta finale per utente.
        Gestisce sia richieste follow-up che raccomandazioni finali.
        """
        assessment = state.get("assessment")
        raccomandazione = state.get("raccomandazione")
        
        if raccomandazione:
            # Risposta finale con raccomandazione
            risposta = f"""**Raccomandazione Specialistica**

**Specialista consigliato**: {raccomandazione.specialista}

**Motivazione clinica**:
{raccomandazione.motivazione}

---
*Questa è una raccomandazione orientativa basata sui sintomi descritti. Per una valutazione completa, consulta sempre un medico.*"""
            
        elif assessment and not assessment.sufficiente:
            # Richiesta follow-up
            risposta = f"""🔍 **Raccolta Informazioni**

{assessment.domanda_followup}

Questo mi aiuterà a indirizzarti verso lo specialista più appropriato per la tua situazione."""
            
        else:
            # Fallback generico
            risposta = """Ciao! Sono il tuo assistente sanitario virtuale. 

Per aiutarti a trovare lo specialista giusto, puoi descrivermi:
• Quali sintomi stai avvertendo
• Da quanto tempo li hai
• Dove si localizzano

Sarò felice di indirizzarti verso la specializzazione più appropriata! 🏥"""
        
        # Aggiungi messaggio AI al thread
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
    """Crea graph triage medico con architettura moderna"""
    
    graph = StateGraph(TriageState)
    
    # Nodi del workflow
    graph.add_node("valuta_completezza", triage_system.valuta_completezza_async)
    graph.add_node("trova_specialista", triage_system.trova_specialista_async)
    graph.add_node("formato_risposta", triage_system.formato_risposta_async)
    
    # Workflow edges (Command pattern gestisce routing)
    graph.add_edge(START, "valuta_completezza")
    
    return graph

# === MEMORY & DEPLOYMENT ===

# Memory globale per persistenza threads
memory = MemorySaver()

# Graph compilato
triage_graph = create_triage_graph().compile(checkpointer=memory)

# === PUBLIC API ===

async def invoke_orchestrator(thread_id: str, message: str) -> str:
    """
    API principale per sistema triage medico.
    
    Compatibile con chat_routes.py esistente.
    Mantiene memoria conversazione per thread_id.
    
    Args:
        thread_id: Identificativo thread per isolamento conversazioni
        message: Messaggio utente da processare
        
    Returns:
        str: Risposta formattata per utente
    """
    try:
        # Configura input per LangGraph
        config = {"configurable": {"thread_id": thread_id}}
        input_data = {
            "messages": [HumanMessage(content=message)]
        }
        
        # Invoca graph asincrono
        logger.info(f"Processing triage for thread {thread_id}: {message[:50]}...")
        
        result = await triage_graph.ainvoke(input_data, config)
        
        # Estrai ultima risposta AI
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                logger.info(f"Triage completed for thread {thread_id}")
                return msg.content
        
        # Fallback se nessuna risposta AI trovata
        return "Mi dispiace, si è verificato un errore. Riprova per favore."
        
    except Exception as e:
        logger.error(f"Errore orchestrator per thread {thread_id}: {e}", exc_info=True)
        return "Mi dispiace, si è verificato un errore tecnico. Riprova tra qualche momento."

# === TESTING UTILITIES ===

async def test_workflow():
    """Test rapido del workflow triage"""
    test_cases = [
        "Ho mal di testa",
        "Ho mal di testa da 3 giorni con nausea",
        "Ho dolore al petto e difficoltà respiratorie"
    ]
    
    for i, test_message in enumerate(test_cases):
        print(f"\n=== Test {i+1}: {test_message} ===")
        response = await invoke_orchestrator(f"test_{i}", test_message)
        print(f"Response: {response}")

if __name__ == "__main__":
    # Test diretto se eseguito standalone
    asyncio.run(test_workflow())