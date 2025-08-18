# app/profissional/routes.py

from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import current_user, login_required
from app.decorators import permission_required
from app.models import Profissional, Acesso, User, db, Condominio
from app.forms import ProfissionalRegistrationForm
from datetime import datetime
import uuid

# Definição do Blueprint
# O 'url_prefix' pode ser omitido aqui e definido apenas em app/__init__.py para evitar redundância.
profissional = Blueprint('profissional', __name__, url_prefix='/profissional', template_folder='templates')

# ==============================================================================
# Rotas de Autenticação e Cadastro
# ==============================================================================

# Rota de Autocadastro para Profissional
# Lida com a criação de um novo registro de Profissional e um novo registro de User.
@profissional.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    form = ProfissionalRegistrationForm()
    
    if form.validate_on_submit():
        # Verifica se o e-mail já está em uso para evitar duplicidade
        email_existente = User.query.filter_by(email=form.email.data).first()
        if email_existente:
            flash('Este e-mail já está cadastrado. Por favor, use outro.', 'danger')
            return redirect(url_for('profissional.cadastro'))

        try:
            # 1. Cria o registro na tabela Profissional
            novo_profissional = Profissional(
                nome=form.nome.data,
                placa_veiculo=form.placa_veiculo.data,
                empresa=form.empresa.data
            )
            db.session.add(novo_profissional)
            db.session.flush() # Obtém o ID do profissional antes do commit

            # 2. Cria o registro na tabela User
            referral_code = str(uuid.uuid4()).replace('-', '')[:8]
            
            novo_usuario_acesso = User(
                nome=form.nome.data,
                email=form.email.data,
                role='profissional',
                profissional_id=novo_profissional.id,
                referral_code=referral_code
            )
            novo_usuario_acesso.set_senha(form.password.data)
            db.session.add(novo_usuario_acesso)
            
            # 3. Vincule a conta de indicação, se existir
            if form.referral_code.data:
                referring_user = User.query.filter_by(referral_code=form.referral_code.data).first()
                if referring_user:
                    novo_usuario_acesso.referred_by = referring_user

            db.session.commit()
            
            flash('Cadastro realizado com sucesso! Você já pode fazer login.', 'success')
            return redirect(url_for('main.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar: {e}', 'danger')
            return redirect(url_for('profissional.cadastro'))

    # Renderiza o formulário de cadastro para a requisição GET
    return render_template('cadastro_profissional.html', form=form)

# ==============================================================================
# Rotas do Painel do Profissional
# ==============================================================================

# NOVO: Rota para exibir o painel do profissional
# Esta rota é a responsável por passar a variável 'profissional' para o template.
@profissional.route('/dashboard')
@login_required
@permission_required('profissional')
def dashboard():
    """
    Exibe o painel do profissional, mostrando suas informações e últimos acessos.
    """
    # Garante que o usuário logado é um profissional e tem um ID de profissional
    if not current_user.profissional_id:
        flash('Sua conta não está associada a um perfil de profissional.', 'danger')
        return redirect(url_for('main.login'))

    # Obtém as informações do profissional e passa para o template
    profissional_info = Profissional.query.get(current_user.profissional_id)
    
    # Obtém os últimos acessos do profissional para exibir na tabela
    ultimos_acessos = Acesso.query.filter_by(profissional_id=profissional_info.id)\
                                  .order_by(Acesso.data_acesso.desc())\
                                  .limit(10)\
                                  .all()

    # A ÚNICA ALTERAÇÃO é aqui, para ser consistente com o nome do arquivo
    return render_template('dashboard_profissional.html',
                           profissional=profissional_info, 
                           ultimos_acessos=ultimos_acessos)

# ==============================================================================
# Rotas de Verificação de QR Code (Pública)
# ==============================================================================

# Rota que será acessada pelo porteiro ao escanear o QR Code
# Esta é uma rota pública para ser acessada sem login
@profissional.route('/perfil_publico/<int:profissional_id>')
def perfil_publico(profissional_id):
    """
    Exibe um perfil público e simplificado do profissional para ser acessado via QR Code.
    """
    profissional = Profissional.query.get_or_404(profissional_id)
    return render_template('perfil_publico.html', profissional=profissional)

# Rota para o checkin do profissional na portaria
@profissional.route('/checkin_portaria/<int:condominio_id>')
@login_required
@permission_required('profissional')
def checkin_portaria(condominio_id):
    """
    Rota para o profissional solicitar entrada ao escanear o QR Code da portaria.
    """
    # 1. Obtenha as informações do profissional logado
    profissional_logado = Profissional.query.get(current_user.profissional_id)

    # 2. Verifique se o condomínio_id é válido
    condominio = Condominio.query.get(condominio_id)
    if not condominio:
        flash('Condomínio não encontrado.', 'danger')
        return redirect(url_for('profissional.dashboard')) # Ou outra página

    try:
        # 3. Crie uma nova entrada na tabela de Acessos com status 'pendente'
        novo_acesso_pendente = Acesso(
            condominio_id=condominio.id,
            profissional_id=profissional_logado.id,
            status='pendente',
            servico='Aguardando verificação',
            data_acesso=datetime.now()
        )
        db.session.add(novo_acesso_pendente)
        db.session.commit()

        # 4. AQUI É ONDE OCORRE A MÁGICA: Enviar a notificação para a tela do porteiro
        # (Isso requer WebSockets ou polling, que faremos mais tarde)
        print(f"Profissional {profissional_logado.nome} solicitou entrada no condomínio {condominio.nome}.")

        flash('Sua solicitação de entrada foi enviada ao porteiro. Por favor, aguarde.', 'info')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao solicitar entrada: {e}', 'danger')
    
    return redirect(url_for('profissional.dashboard'))