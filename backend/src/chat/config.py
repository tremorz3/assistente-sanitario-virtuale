import os

# Endpoint Ollama
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

# Modelli
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.1:8b-instruct-q6_K")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "snowflake-arctic-embed2")

