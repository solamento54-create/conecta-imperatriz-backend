FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema (para psycopg2 e Pillow)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY . .

# Porta usada (Railway/Fly substituem via $PORT)
EXPOSE 8000

# Inicia o servidor
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
