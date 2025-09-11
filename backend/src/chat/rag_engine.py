"""
RAGEngine - Motore RAG per Raccomandazioni Specialisti Medici

Sistema RAG (Retrieval-Augmented Generation) ottimizzato per raccomandazioni
specialistiche basato su vector search + LLM analysis.

Architettura:
1. Vector Search (FAISS) per sintomi simili 
2. Context Retrieval da knowledge base medico
3. LLM Analysis per raccomandazione strutturata
4. Fallback robusti per affidabilità produzione
"""

import logging
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from .config import LLM_MODEL, OLLAMA_BASE_URL
from .vector_store import get_retriever
from pydantic import BaseModel, Field

class SpecialistRecommendation(BaseModel):
    """Schema per raccomandazione specialista"""
    specialista: str = Field(description="Nome specialista raccomandato")
    motivazione: str = Field(description="Ragionamento clinico dettagliato")

logger = logging.getLogger(__name__)

class RAGEngine:
    """Motore RAG per raccomandazioni specialisti medici"""
    
    def __init__(self):
        self.llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0  # Deterministic per consistency clinica
        )
        
        self.recommendation_prompt = ChatPromptTemplate.from_template("""
Sei un medico AI specializzato nell'orientamento verso specialisti appropriati.

Analizza i sintomi descritti dall'utente utilizzando il contesto medico fornito dal database
per raccomandare lo specialista più appropriato.

CONTESTO DAL DATABASE MEDICO:
{context}

SINTOMI DESCRITTI DALL'UTENTE:
{symptoms}

ISTRUZIONI:
1. Analizza i sintomi in relazione alle competenze degli specialisti nel contesto
2. Identifica il pattern sintomatologico principale
3. Raccomanda lo specialista più appropriato per quel pattern
4. Fornisci motivazione clinica chiara, professionale e dettagliata

Sii professionale ma accessibile. Evita diagnosi specifiche, concentrati sulla direzione specialistica.
        """)
    
    async def find_specialist(self, symptoms_text: str) -> SpecialistRecommendation:
        """
        Trova specialista appropriato usando RAG analysis.
        
        Args:
            symptoms_text: Testo completo sintomi da analizzare
            
        Returns:
            SpecialistRecommendation: Raccomandazione strutturata con motivazione
        """
        try:
            # FASE 1: Vector Retrieval
            logger.debug(f"Starting RAG analysis for symptoms: {symptoms_text[:100]}...")
            
            retriever = get_retriever(k_results=5)
            relevant_docs = retriever.get_relevant_documents(symptoms_text)
            
            if not relevant_docs:
                logger.warning("No relevant documents found in vector search")
                return self._fallback_recommendation()
            
            # FASE 2: Context Preparation
            context_str = "\n".join([doc.page_content for doc in relevant_docs])
            logger.debug(f"Retrieved {len(relevant_docs)} docs, context length: {len(context_str)}")
            
            # FASE 3: LLM Analysis con Structured Output
            structured_llm = self.llm.with_structured_output(SpecialistRecommendation)
            rag_chain = self.recommendation_prompt | structured_llm
            
            recommendation = await rag_chain.ainvoke({
                "context": context_str,
                "symptoms": symptoms_text
            })
            
            logger.info(f"RAG recommendation: {recommendation.specialista}")
            return recommendation
            
        except Exception as e:
            logger.error(f"RAG engine error: {e}")
            return self._fallback_recommendation()
    
    def _fallback_recommendation(self) -> SpecialistRecommendation:
        """Raccomandazione di sicurezza quando RAG fallisce"""
        return SpecialistRecommendation(
            specialista="Medico di Medicina Generale",
            motivazione="""Si è verificato un problema nell'analisi automatica dei sintomi. 

Ti consiglio di consultare il tuo Medico di Medicina Generale che potrà:
• Effettuare una valutazione clinica completa
• Considerare la tua storia medica personale  
• Indirizzarti verso lo specialista più appropriato se necessario

Il medico di base è sempre il punto di partenza ideale per un inquadramento iniziale."""
        )
    
    async def test_rag_pipeline(self):
        """Test rapido del pipeline RAG"""
        test_symptoms = [
            "mal di testa pulsante con nausea",
            "dolore al petto con affanno",
            "dolore addominale localizzato"
        ]
        
        for symptoms in test_symptoms:
            logger.info(f"Testing RAG with: {symptoms}")
            result = await self.find_specialist(symptoms)
            logger.info(f"Result: {result.specialista} - {result.urgenza}")

if __name__ == "__main__":
    import asyncio
    
    async def test():
        engine = RAGEngine()
        await engine.test_rag_pipeline()
    
    asyncio.run(test())