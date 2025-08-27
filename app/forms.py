# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DecimalField, IntegerField, TextAreaField, DateField, FloatField, BooleanField
from wtforms.validators import DataRequired, Email, ValidationError, Optional, Length, NumberRange, EqualTo, Regexp
from app.models import User, Profissional

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class UserForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha')
    confirm_password = PasswordField('Confirme a Senha')
    role = SelectField('Nível de Acesso', choices=[('admin', 'Administrador'), ('sindico', 'Síndico'), ('porteiro', 'Porteiro'), ('morador', 'Morador')], validators=[DataRequired()])
    condominio_id = SelectField('Condomínio', coerce=int, validators=[Optional()])
    apartamento = StringField('Apartamento')
    submit = SubmitField('Criar Usuário')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        
        # O self.submit.data é True apenas durante a submissão, mas o form.obj existe no GET
        # Se form.obj.email existe (edição), e o email no form não mudou, ignore a validação.
        # Caso contrário, verifique se o email já existe.
        if user and hasattr(self, 'obj') and user.id != self.obj.id:
             raise ValidationError('Este email já está cadastrado. Por favor, use outro.')

    def validate_password(self, password):
        """
        Valida a senha e a confirmação de senha.
        Se a senha for fornecida, a confirmação também deve ser igual.
        Se a senha estiver vazia (edição), a confirmação é ignorada.
        """
        # Apenas valida se uma nova senha foi fornecida
        if password.data:
            if not self.confirm_password.data:
                raise ValidationError('Por favor, confirme a nova senha.')
            if password.data != self.confirm_password.data:
                raise ValidationError('A senha e a confirmação de senha não coincidem.')
        # Se a senha for vazia, a confirmação também deve ser
        elif self.confirm_password.data:
            raise ValidationError('Confirmação de senha fornecida, mas a senha não foi preenchida.')

class CondominioForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    endereco = StringField('Endereço', validators=[DataRequired()])
    tipo = SelectField('Tipo', validators=[DataRequired()], choices=[('casa', 'Casa'), ('apartamento', 'Apartamento')])
    status_assinatura = SelectField('Status da Assinatura', choices=[('ativa', 'Ativa'), ('inativa', 'Inativa'), ('suspensa', 'Suspensa')], validators=[DataRequired()])
    plano_id = SelectField('Plano', coerce=int, validators=[Optional()])
    submit = SubmitField('Salvar')

class AutorizarAcessoForm(FlaskForm):
    """Formulário para o morador pré-autorizar um acesso."""
    servico = StringField('Serviço', validators=[DataRequired(), Length(max=256)])
    empresa = StringField('Empresa', validators=[Length(max=256)])
    data_prevista_acesso = DateField('Data Prevista do Acesso', format='%Y-%m-%d', validators=[DataRequired()])
    observacoes_morador = TextAreaField('Observações', validators=[Length(max=512)])
    submit = SubmitField('Autorizar Acesso')

class RelatorioAcessoForm(FlaskForm):
    data_inicio = DateField('Data de Início', format='%Y-%m-%d', validators=[DataRequired()])
    data_fim = DateField('Data de Fim', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Gerar Relatório')

class ProfissionalForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    placa_veiculo = StringField('Placa do Veículo')
    empresa = StringField('Empresa')
    url_foto = StringField('URL da Foto')
    submit = SubmitField('Cadastrar Profissional')

class RegistrarAcessoForm(FlaskForm):
    """Formulário para o porteiro registrar um acesso de um profissional já cadastrado."""
    morador_id = SelectField('Morador Autorizador', coerce=int, validators=[DataRequired()])
    servico = StringField('Serviço', validators=[DataRequired(), Length(max=256)])
    submit = SubmitField('Registrar Entrada')

class EntradaManualForm(FlaskForm):
    cpf = StringField('CPF do Profissional', validators=[DataRequired(), Length(min=11, max=14)])
    submit = SubmitField('Registrar Entrada')

class PlanoForm(FlaskForm):
    nome = StringField('Nome do Plano', validators=[DataRequired()])
    valor_mensal = DecimalField('Valor Mensal', validators=[DataRequired(), NumberRange(min=0)])
    dias_carencia = IntegerField('Dias de Carencia', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Salvar Plano')

class CondominioPlanoForm(FlaskForm):
    plano_id = SelectField('Plano de Assinatura', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Alterar Plano')

# Formularios para cadastro dos profissinais



# Adicionar a validação para CPF
def validate_cpf(form, field):
    cpf = field.data.replace('.', '').replace('-', '')
    if not cpf.isdigit() or len(cpf) != 11:
        raise ValidationError('CPF inválido. Use apenas números.')

# Formulário de Cadastro do Profissional
class ProfissionalRegistrationForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=128)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password_confirm = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password', message='As senhas devem ser iguais.')])
    placa_veiculo = StringField('Placa do Veículo (Opcional)', validators=[Length(max=10)])
    empresa = StringField('Empresa', validators=[DataRequired(), Length(min=2, max=128)])
    referral_code = StringField('Código de Indicação (Opcional)')
    submit = SubmitField('Cadastrar')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este email já está cadastrado. Por favor, use um email diferente.')

    def validate_cpf_exists(self, cpf):
        profissional = Profissional.query.filter_by(cpf=cpf.data).first()
        if profissional is not None:
            raise ValidationError('Já existe um profissional cadastrado com este CPF.')
        
class PortariaForm(FlaskForm):
    nome = StringField('Nome da Portaria', validators=[DataRequired()])
    submit = SubmitField('Salvar')