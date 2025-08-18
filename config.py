# config.py
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """
    Classe de configuração base para a aplicação.
    As variáveis são carregadas do arquivo .env.
    """
    SECRET_KEY = os.environ.get('DB_PASSWORD') or 'uma_chave_super_secreta_e_dificil_de_adivinhar'
    
    # URL de conexão com o banco de dados.
    # A variável de ambiente DATABASE_URL é a preferida.
    # A URL padrão usa PostgreSQL com o nome do banco 'easygate'.
    # Certifique-se de que o usuário, senha e o host estão corretos de acordo com o seu Docker.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/easygate'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False