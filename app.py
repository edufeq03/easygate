from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from app.forms import LoginForm
from app.models import User, Plano, Condominio, Profissional

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# -----------------
# Flask-Login
# -----------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Define a rota para a pagina de login
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# Importa os modelos depois de db ser inicializado
from app.models import User, Plano, Condominio, Profissional

# Esta funcao é exigida pelo Flask-Login para carregar o usuario
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# -----------------

@app.route('/')
def index():
    return render_template('index.html')

#


if __name__ == '__main__':
    app.run(debug=True)