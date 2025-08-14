FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libmariadb-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src/ .
# Copia anche lo script di seeding per renderlo accessibile dal backend
COPY mariadb_init/seeder.py ./

CMD ["sh", "-c", "python seeder.py && exec uvicorn main:app --host 0.0.0.0 --port 8001"]

HEALTHCHECK --interval=1m --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import sys, http.client; conn = http.client.HTTPConnection('localhost', 8001); conn.request('GET', '/'); sys.exit(0) if conn.getresponse().status == 200 else sys.exit(1)"
