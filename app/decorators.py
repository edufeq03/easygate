# app/decorators.py

from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def permission_required(*roles): # Adicione o asterisco para aceitar múltiplos argumentos
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403) # Proibe o acesso se o papel do usuário não estiver na lista
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==============================================================================
# Decorador para restringir acesso a usuários com o papel (role) de 'sindico'
# ==============================================================================
def sindico_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Primeiro, verifica se o usuário está logado
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('main.login'))
        
        # Em seguida, verifica se o papel (role) do usuário é 'sindico'
        if current_user.role != 'sindico':
            flash('Você não tem permissão para acessar esta página.', 'danger')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function