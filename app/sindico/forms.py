# app/sindico/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

# ==============================================================================
# Formulário para usuários (porteiro) do síndico
# ==============================================================================
class UserForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=128)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=128)])
    # A senha é opcional, pois não é necessário alterá-la na edição de um usuário.
    # No entanto, na criação, ela deve ser obrigatória. 
    # Usamos o validador Optional() para permitir que o campo fique vazio
    # e tratamos a obrigatoriedade na rota.
    senha = PasswordField('Senha', validators=[Optional(), Length(min=6, max=256)])
    
    # Este campo será preenchido dinamicamente na rota
    portaria = SelectField('Portaria', coerce=int, validators=[DataRequired()])