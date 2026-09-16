FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema necessárias para mysqlclient
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 5000

# Comando para rodar
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
