from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate  # <-- Adicionada a importação
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # <-- Adicionada a instância de Migrate

from app.models import User

@login_manager.user_loader
def load_user(user_id):
    # Esta função carrega o usuário do banco de dados pelo ID
    return User.query.get(int(user_id))
# ---------------------------------------------

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # <-- Adicionada a inicialização
    
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app