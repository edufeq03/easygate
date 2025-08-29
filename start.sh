#!/bin/sh
# Espera 10 segundos para garantir que o banco de dados esteja totalmente pronto
echo "Waiting for database to start..."
sleep 20

# Aguarda o banco de dados estar pronto
echo "Aguardando o banco de dados..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Banco de dados pronto. Rodando migrações..."

# Roda as migrações do banco de dados antes de iniciar a aplicação
flask db upgrade

# Inicia o servidor Gunicorn, apontando para o arquivo 'run.py' e a variável 'app'
exec gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --bind 0.0.0.0:5001 --timeout 120 run:app
