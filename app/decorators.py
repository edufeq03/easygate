# app/decorators.py

from functools import wraps
from flask import abort
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