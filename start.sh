#!/bin/sh

# Espera o banco de dados ficar pronto
until pg_isready -h db -p 5432 -U "$DB_USER"; do
  echo "Aguardando o banco de dados..."
  sleep 1
done

echo "Banco de dados pronto. Rodando migrações..."

# Aplica as migrações mais recentes
flask db upgrade

# Executa o comando principal da sua aplicação
exec gunicorn --bind 0.0.0.0:5001 --workers 3 --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker run:app