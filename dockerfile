# Usa uma imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos e o instala para aproveitar o cache do Docker
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos da sua aplicação
COPY . .

# Expõe a porta que o Gunicorn irá usar
EXPOSE 5001

# Define o comando para iniciar a aplicação com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "3", "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "run:app"]
 