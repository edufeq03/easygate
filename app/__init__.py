# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
#from flask_bootstrap4 import Bootstrap4 # Importa a extensão do Bootstrap4

# Importa a classe de configuração
from config import Config

# Criando as instâncias das extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
#bootstrap = Bootstrap4()

def create_app(config_class=Config):
    # Definir caminho da pasta template, se o __init__.py estiver dentro de app/
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(config_class)

    # Configuração para que o login_manager redirecione corretamente
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    #bootstrap.init_app(app)
    # Importante: Inicializa o SocketIO com a app
    # A opção cors_allowed_origins é importante para desenvolvimento
    socketio.init_app(app, cors_allowed_origins="*")

    # Registro dos Blueprints
    # O Blueprint 'main' é o principal e deve ser registrado primeiro
    from app import routes as main_routes
    app.register_blueprint(main_routes.main) # Usa o alias 'bp' para o Blueprint principal

    # Blueprints para cada tipo de usuário
    from app.porteiro import routes as porteiro_routes
    app.register_blueprint(porteiro_routes.porteiro)

    from app.profissional import routes as profissional_routes
    app.register_blueprint(profissional_routes.profissional)

    from app.sindico import routes as sindico_routes
    app.register_blueprint(sindico_routes.sindico)

    # User loader function for Flask-Login
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Contexto para o Flask shell (útil para depuração)
    from app.models import User, Condominio, Profissional, Acesso, Portaria, Plano
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': User, 'Condominio': Condominio, 'Profissional': Profissional, 'Acesso': Acesso, 'Portaria': Portaria, 'Plano': Plano}

    return app