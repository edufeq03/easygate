# create_db.py
from app import create_app, db

# 1. Cria a instância da aplicação Flask
app = create_app()

# 2. Entra no contexto da aplicação para executar comandos
with app.app_context():
    print("Criando todas as tabelas do banco de dados...")
    db.create_all()
    print("Tabelas criadas com sucesso!")