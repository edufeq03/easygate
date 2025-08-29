# Usa uma imagem base oficial do Python
FROM python:3.10-slim

# Instala o cliente PostgreSQL e o Netcat em um único comando
RUN apt-get update && \
    apt-get install -y postgresql-client netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos e o instala para aproveitar o cache do Docker
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos da sua aplicação
COPY . .

# Torna o script executável
RUN chmod +x /app/start.sh

# Expõe a porta que o Gunicorn irá usar
EXPOSE 5001

# Usa ENTRYPOINT para garantir que o comando de inicialização seja sempre executado.
# A diferença entre ENTRYPOINT e CMD é sutil, mas para scripts de inicialização,
# o ENTRYPOINT é a melhor prática.
ENTRYPOINT ["/app/start.sh"]