from fastapi import FastAPI

app = FastAPI(
    title="Assistente Virtuale Sanitario API",
    description="API per la gestione dell'orientamento sanitario, autenticazione e servizi correlati.",
    version="0.0.1"
)

"""
Nota: "async" permette a una funzione di "sospendersi" in attesa che un'operazione che richiede tempo sia completata, 
e nel frattempo, il programma può eseguire altro codice.
"""

@app.get("/")
async def read_root():
    return {"message": "Benvenuto nell'Assistente Virtuale Sanitario!"}