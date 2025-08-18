#!/bin/bash

# ===============================================
# Script de inicialização do ambiente de desenvolvimento EasyGate
# Este script automatiza o start do banco de dados e da aplicação.
# ===============================================

# 1- Subir o container Docker
echo "1. Subindo Docker Container..."
docker-compose up -d

# 2- Ativar o ambiente virtual (venv)
echo "2. Ativando o ambiente virtual..."
source venv/bin/activate

# 3. Executar o script de criação do banco de dados:
echo "3. Executando o script de criação do banco de dados..."
python3 create_db.py


# 4. Iniciar a aplicação Flask
#echo "4. Iniciando a aplicação Flask..."
#flask run

echo "Processo concluído."