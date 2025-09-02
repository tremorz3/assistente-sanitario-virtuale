"""
RAG-Based Medical Specialist Tool for LangGraph Agent

Implementa uno strumento AI che utilizza Retrieval-Augmented Generation (RAG)
per raccomandare specialisti medici basandosi sui sintomi descritti dall'utente.

Processo RAG:
1. Vector Similarity Search: Cerca sintomi simili nel knowledge base medico
2. Context Retrieval: Recupera descrizioni specialisti più pertinenti  
3. LLM Analysis: Analizza sintomi + contesto per generare raccomandazione strutturata
4. Structured Output: Restituisce specialista + motivazione clinica
"""

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.chat_models import ChatOllama
from .vector_store import get_retriever
from .config import LLM_MODEL, OLLAMA_BASE_URL
from pydantic import BaseModel, Field

class SpecialistResponse(BaseModel):
    """
    Schema strutturato per l'output del tool find_specialist.
    Garantisce che l'AI restituisca sempre specialista + motivazione clinica.
    """
    specialist: str = Field(description="Nome dello specialista medico raccomandato (es: Neurologia, Cardiologia)")
    reasoning: str = Field(description="Ragionamento clinico dettagliato che spiega perché questo specialista è appropriato")

class FindSpecialistArgs(BaseModel):
    """Schema input per il tool find_specialist."""
    sintomi: str = Field(
        ...,
        description=(
            "Testo libero con i sintomi principali, durata, localizzazione e "
            "eventuali sintomi associati (se presenti)."
        ),
    )

@tool("find_specialist", args_schema=FindSpecialistArgs)
def find_specialist(sintomi: str) -> dict:
    """
    Raccomanda lo specialista medico dato un testo di sintomi.

    Quando usarlo:
    - Usa questo tool quando l'utente descrive sintomi/problemi di salute o chiede
      a quale specialista rivolgersi.

    Input richiesto:
    - "sintomi": testo libero con sintomi, durata, localizzazione e sintomi associati.

    Output:
    - Dizionario con "specialist" (es. Cardiologia) e "reasoning" (motivazione clinica).
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Executing RAG specialist finder with symptoms: {sintomi[:100]}...")
    
    # === VALIDAZIONE INPUT ===
    # Previene esecuzione con dati vuoti/fittizi che potrebbero causare raccomandazioni errate
    if not sintomi or not str(sintomi).strip() or str(sintomi).strip().lower() in {"nessun sintomo descritto", "", "n/a", "na"}:
        return {
            "specialist": "Informazioni insufficienti",
            "reasoning": (
                "Per indirizzarti allo specialista giusto ho bisogno di informazioni più dettagliate: "
                "quali sono i sintomi specifici, da quanto tempo sono presenti e dove si localizzano."
            ),
        }
    
    # === FASE 1: VECTOR RETRIEVAL ===
    # Utilizza FAISS per trovare descrizioni specialisti più simili ai sintomi input
    retriever = get_retriever()  # Carica il vector store medico
    docs = retriever.get_relevant_documents(sintomi)  # Similarity search
    
    # Fallback se il vector search non trova documenti pertinenti
    if not docs:
        return {
            "specialist": "Medico di Medicina Generale", 
            "reasoning": "Non ho trovato corrispondenze specifiche nel database. Ti consiglio di iniziare con un consulto generale per un primo inquadramento."
        }

    # === FASE 2: LLM ANALYSIS ===
    # Usa un LLM separato per analizzare documenti recuperati + sintomi utente
    # Temperature=0 per raccomandazioni deterministiche e coerenti
    llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    
    # PROMPT ENGINEERING: Istruzioni precise per l'analisi clinica
    extraction_prompt = ChatPromptTemplate.from_template(
        """Analizza i sintomi dell'utente utilizzando il contesto medico fornito per raccomandare lo specialista più appropriato.

        Contesto dal knowledge base medico:
        {context}

        Sintomi descritti dall'utente:
        {symptoms}

        Fornisci una raccomandazione basata su:
        1. Corrispondenza tra sintomi e expertise dello specialista
        2. Approccio clinico prudente e sicuro
        3. Se il contesto è limitato, prediligi specialisti generici
        """
    )

    # Combina documenti recuperati in context unificato per LLM
    context_str = "\n".join([doc.page_content for doc in docs])

    logger.debug(f"RAG context prepared - {len(docs)} docs, {len(context_str)} chars, symptoms: {sintomi[:50]}...")

    # === FASE 3: STRUCTURED OUTPUT GENERATION ===
    # Approccio multi-livello per garantire output strutturato affidabile
    
    try:
        # METODO PRIMARIO: Function calling (più affidabile con Ollama)
        structured_llm = llm.with_structured_output(
            SpecialistResponse,
            method="function_calling",  # Sfrutta function calling nativo del modello
            include_raw=False  # Restituisce solo il risultato strutturato
        )
        
        # Catena: Prompt + Context + Symptoms → Structured LLM → SpecialistResponse
        extraction_chain = extraction_prompt | structured_llm
        
        result = extraction_chain.invoke({
            "context": context_str,  # Documenti da vector search
            "symptoms": sintomi,     # Input utente originale
        })
        
        logger.debug("Successfully generated specialist recommendation via function calling")
        return result.model_dump() if hasattr(result, 'model_dump') else result
        
    except Exception as function_calling_error:
        logger.warning(f"Function calling failed: {function_calling_error}")
        
        # METODO FALLBACK 1: Structured output semplificato (senza function calling)
        try:
            structured_llm = llm.with_structured_output(SpecialistResponse)
            extraction_chain = extraction_prompt | structured_llm
            
            result = extraction_chain.invoke({
                "context": context_str,
                "symptoms": sintomi,
            })
            
            logger.debug("Generated specialist recommendation via simplified structured output")
            return result.model_dump() if hasattr(result, 'model_dump') else result
            
        except Exception as structured_error:
            logger.error(f"All structured output methods failed: {structured_error}")
            raise structured_error

    except Exception as e:
        # === FALLBACK FINALE ===
        # Quando tutti i metodi structured output falliscono, restituisce raccomandazione sicura
        logger.error(f"RAG tool complete failure - Model: {LLM_MODEL}, Error: {type(e).__name__}: {e}")
        logger.error(f"Symptoms context: {sintomi[:100]}...")
        
        # Raccomandazione di sicurezza: sempre prudente indirizzare al medico generale
        # quando il sistema automatico non può fornire analisi affidabile
        fallback_reasoning = (
            "Si è verificato un problema tecnico nell'analisi automatica dei sintomi descritti. "
            "Per una valutazione appropriata, ti consiglio di consultare il tuo Medico di Medicina Generale "
            "che potrà effettuare un inquadramento completo e, se necessario, indirizzarti verso lo specialista più adatto."
        )
        
        return {
            "specialist": "Medico di Medicina Generale",
            "reasoning": fallback_reasoning,
        }
