# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from flask_socketio import SocketIO

# Importa a classe de configuração
from config import Config

# Criando as instâncias das extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_class=Config):
    #Definir caminho da pasta template, se o __init__.py estiver dentro de app/
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(config_class)

    # Configuração para que o login_manager redirecione corretamente
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # Importante: Inicializa o SocketIO com a app
    # A opção cors_allowed_origins é importante para desenvolvimento
    socketio.init_app(app, cors_allowed_origins="*")

    # Registro dos Blueprints
    # O Blueprint 'main' pode estar em app/main/routes.py, por exemplo
    from app import routes as main_routes
    app.register_blueprint(main_routes.main)

    # Blueprints para cada tipo de usuário
    from app.porteiro import routes as porteiro_routes
    from app.profissional import routes as profissional_routes
    from app import routes as admin_routes
    
    app.register_blueprint(porteiro_routes.porteiro)
    app.register_blueprint(profissional_routes.profissional)
    #app.register_blueprint(admin_routes.main)

    # User loader function for Flask-Login
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Contexto para o Flask shell (útil para depuração)
    from app.models import User, Condominio, Profissional, Acesso
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': User, 'Condominio': Condominio, 'Profissional': Profissional, 'Acesso': Acesso}

    return app