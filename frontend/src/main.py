
from fastapi import FastAPI

# Importiamo i nostri router finali
from routers import auth_routes,chat_routes, proxy_routes

app = FastAPI(title="Assistente Virtuale Sanitario Web Server")

# Includiamo i router nell'applicazione principale
app.include_router(auth_routes.router)
app.include_router(chat_routes.router)
app.include_router(proxy_routes.router)