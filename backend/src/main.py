from fastapi import FastAPI

# Import dei router
from routers import disponibilita_routes, auth_routes, chat_routes, general_routes, prenotazioni_routes, valutazioni_routes

app = FastAPI(
    title="Assistente Virtuale Sanitario API",
    description="API per la gestione dell'orientamento sanitario, autenticazione e servizi correlati.",
)

# Include i routers nell'applicazione principale
# Nota un router è una mini applicazione FastAPI che gestisce un sottoinsieme di URL
app.include_router(disponibilita_routes.router)
app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(general_routes.router)
app.include_router(prenotazioni_routes.router)
app.include_router(valutazioni_routes.router)

@app.get("/")
async def read_root():
    return {"message": "Benvenuto nell'API dell'Assistente Virtuale Sanitario!"}
