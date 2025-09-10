# chat/vector_store.py
"""
FAISS Vector Store for Medical Knowledge Base

Implementa un sistema di ricerca semantica per specialisti medici utilizzando:
1. FAISS (Facebook AI Similarity Search) per indicizzazione vettoriale
2. Ollama embeddings per rappresentazione semantica dei testi
3. Knowledge base CSV con mappature sintomi → specialisti
4. Chunking intelligente per ottimizzare precision del retrieval

Architettura: CSV → Text Chunks → Vector Embeddings → FAISS Index → Similarity Search
"""

import os
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import CSVLoader
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .config import EMBED_MODEL, OLLAMA_BASE_URL

# === CONFIGURAZIONE PATHS ===
# Knowledge base e indice FAISS nella directory vectordb locale
current_dir = os.path.dirname(__file__)
KB_PATH = os.path.join(current_dir, "vectordb", "kb_spec.csv")  # CSV con sintomi-specialisti
INDEX_PATH = os.path.join(current_dir, "vectordb", "langchain_faiss_index")  # Indice persistente

def get_retriever(k_results=5):
    """
    Factory per il retriever FAISS: carica indice esistente o lo crea da zero.
    
    Strategia lazy loading:
    - Se l'indice FAISS esiste → caricamento rapido dalla cache  
    - Se non esiste → creazione completa da CSV (più lenta, solo primo run)
    
    Il retriever utilizza similarity search cosine per trovare i documenti
    più semanticamente simili ai sintomi query dell'utente.

    Args:
        k_results (int): Numero di documenti da recuperare (default 5)
                        Valori più alti = più contesto ma potenziale rumore

    Returns:
        LangChain retriever pronto per .get_relevant_documents(query)
    """
    # === INIZIALIZZAZIONE EMBEDDINGS ===
    try:
        # Configura Ollama embeddings per conversione testo → vettori semantici
        # Modello snowflake-arctic-embed2 è ottimizzato per domini specifici come medicina
        embeddings = OllamaEmbeddings(
            model=EMBED_MODEL,       # Modello embedding da config
            base_url=OLLAMA_BASE_URL # Endpoint Ollama service
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize Ollama embeddings - Model: {EMBED_MODEL}, URL: {OLLAMA_BASE_URL}, Error: {e}")
        raise ValueError(f"Cannot connect to Ollama embedding service. Ensure Ollama is running and model '{EMBED_MODEL}' is available.")

    # === CARICAMENTO O CREAZIONE INDICE ===
    
    if os.path.exists(INDEX_PATH):
        # CASO 1: Indice già esistente - caricamento veloce
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Loading pre-built FAISS index from cache...")
        
        # Carica indice FAISS persistente (include embeddings + metadati)
        # allow_dangerous_deserialization=True necessario per deserializzare pickle FAISS
        vector_store = FAISS.load_local(
            INDEX_PATH, 
            embeddings, 
            allow_dangerous_deserialization=True  # Sicuro nel nostro caso controllato
        )
    else:
        # CASO 2: Prima esecuzione - creazione completa da CSV
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Building new FAISS index from knowledge base CSV...")
        
        # STEP 1: Caricamento CSV knowledge base
        # specializzazione come source_column per tracking origine documento
        loader = CSVLoader(
            file_path=KB_PATH, 
            source_column="specializzazione",  # Identifica specialista di origine
            csv_args={"delimiter": ",", "quotechar": '"'}  # Parsing CSV standard
        )
        documents = loader.load()  # Lista di Document objects con content + metadata
        
        # STEP 2: Text Chunking per ottimizzazione retrieval
        # Chunks più piccoli = maggiore precision, meno context per chunk
        # 500 char + 50 overlap = bilanciamento precision/context per dominio medico
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,   # Dimensione target per chunk (caratteri)
            chunk_overlap=50  # Overlap per preservare continuità semantica
        )
        docs = text_splitter.split_documents(documents)
        
        # STEP 3: Creazione indice FAISS
        # Converte ogni chunk in embedding vettoriale e costruisce indice per similarity search
        vector_store = FAISS.from_documents(docs, embeddings)
        
        # STEP 4: Persistenza per future esecuzioni
        vector_store.save_local(INDEX_PATH)
        logger.info(f"FAISS index built successfully with {len(docs)} chunks")

    # === CONFIGURAZIONE RETRIEVER ===
    # Converte vector store in retriever per interfaccia LangChain standard
    # search_kwargs configura il comportamento della similarity search
    return vector_store.as_retriever(
        search_kwargs={"k": k_results}  # Restituisce top-k documenti più simili
    )