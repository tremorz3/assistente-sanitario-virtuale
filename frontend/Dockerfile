FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libmariadb-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Imposta la directory di lavoro
WORKDIR /app

# Copia e installa i requisiti Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente dalla cartella 'src' alla directory di lavoro '/app'
COPY src/ .

# Copia la cartella dei template in '/app/templates'
COPY templates/ ./templates/

# Comando per avviare l'applicazione.
# Dato che 'main.py' è ora in '/app', non serve più specificare 'src.'
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]