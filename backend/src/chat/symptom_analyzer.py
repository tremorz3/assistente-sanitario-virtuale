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
    """Schema di risposta per valutazione completezza sintomi"""
    soddisfatto: bool = Field(description="True se utente ha fornito tutte le informazioni necessarie")
    domanda_followup: Optional[str] = Field(description="Domanda specifica per raccogliere informazioni mancanti, null se completo")

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
Sei un assistente medico per triage orientativo. Leggi questa conversazione:

{conversation_history}

Valuta se hai le informazioni necessarie per raccomandare il medico specialista adeguato

VALUTAZIONE:
- Se utente ti ha fornito una descrizione chiara del problema di salute → soddisfatto = true, domanda_followup = null
- Se le informazioni dell'utente non ti rendono chiaro il problema→ soddisfatto = false, fai UNA domanda per disambiguare

Fai MASSIMO 2-3 domande, poi considera le informazioni sufficienti.
""")
    
    async def assess_completeness(self, conversation_history: List[BaseMessage], tentativo_numero: int = 1) -> CompletenessAssessment:
        """
        Valuta completezza informazioni sintomi usando AI structured output progressivo.
        
        Args:
            conversation_history: Cronologia completa messaggi della conversazione
            tentativo_numero: Numero tentativo corrente (progressivo)
            
        Returns:
            CompletenessAssessment: Valutazione strutturata con domande follow-up intelligenti
        """
        try:
            # Estrai TUTTA la conversazione (utente + bot) per contesto completo
            full_conversation = []
            for i, msg in enumerate(conversation_history):
                if isinstance(msg, HumanMessage):
                    full_conversation.append(f"Utente: {msg.content}")
                    logger.info(f"[{i}] USER: {msg.content}")
                elif hasattr(msg, 'content') and msg.content:
                    full_conversation.append(f"Bot: {msg.content}")
                    logger.info(f"[{i}] AI: {msg.content[:100]}...")
            
            history_text = "\n".join(full_conversation) if full_conversation else "(Nessuna cronologia precedente)"
            logger.info(f"=== SYMPTOM ANALYZER INPUT ===")
            logger.info(f"Total conversation turns: {len(full_conversation)}")
            logger.info(f"History text length: {len(history_text)}")
            logger.info(f"=== SENDING TO LLM ===")
            logger.info(f"Full history text:\n{history_text}")
            logger.info(f"==================================")
            
            # Structured LLM per output affidabile
            structured_llm = self.llm.with_structured_output(CompletenessAssessment)
            assessment_chain = self.assessment_prompt | structured_llm
            
            logger.debug(f"Analyzing symptom completeness for {len(full_conversation)} conversation turns...")
            
            result = await assessment_chain.ainvoke({
                "conversation_history": history_text,
                "tentativo_numero": tentativo_numero
            })
            
            logger.info(f"Completeness assessment: soddisfatto={result.soddisfatto}")
            logger.info(f"Generated follow-up question: '{result.domanda_followup}'")
            return result
            
        except Exception as e:
            logger.error(f"Error in symptom analysis: {e}")
            # Fallback conservativo: domanda specifica per primo contatto
            return CompletenessAssessment(
                soddisfatto=False,
                domanda_followup="Per aiutarti al meglio, puoi descrivermi che tipo di disturbo o fastidio stai avvertendo?"
            )
