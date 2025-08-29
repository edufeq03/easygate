# app/routes.py
# Este arquivo define as rotas principais da aplicação e as rotas
# que não se encaixam em outros módulos específicos (ex: admin e morador).

from flask import render_template, redirect, url_for, flash, Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import generate_csrf
from datetime import datetime, timedelta
from app.decorators import permission_required
from app.models import User, Condominio, db, Plano
from app.forms import (
    LoginForm,
    AutorizarAcessoForm,
    UserForm,
    CondominioForm,
    PlanoForm,
    CondominioPlanoForm
)
from app.services import (
    criar_pre_autorizacao,
    get_acessos_morador,
    create_user_admin,
    create_condominio_admin,
    get_all_users,
    get_all_planos,
    get_all_condominios,
    get_user_by_id,
    update_user_admin,
    delete_user_admin,
    get_condominio_by_id,
    update_condominio_admin,
    delete_condominio_admin,
)

# ==============================================================================
# Define o Blueprint principal da aplicação
# O nome da variável foi alterado para 'main' para evitar erros de importação
# ==============================================================================
main = Blueprint('main', __name__)

# ==================================
# Rotas de Autenticação e Index
# ==================================
@main.route('/')
@main.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'sindico':
            return redirect(url_for('sindico.sindico_dashboard'))
        elif current_user.role == 'porteiro':
            return redirect(url_for('porteiro.porteiro_dashboard'))
        elif current_user.role == 'morador':
            return redirect(url_for('main.morador_dashboard'))
        # elif current_user.role == 'profissional':
        #     return redirect(url_for('profissional.dashboard'))
    now = datetime.now()
    return render_template('index.html', now=now)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_senha(form.password.data):
            flash('Email ou senha inválidos', 'danger')
            return redirect(url_for('main.login'))
        
        login_user(user)
        flash('Login realizado com sucesso!', 'success')
        
        if user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif user.role == 'sindico':
            return redirect(url_for('sindico.sindico_dashboard'))
        elif user.role == 'porteiro':
            return redirect(url_for('porteiro.porteiro_dashboard'))
        elif user.role == 'morador':
            return redirect(url_for('main.morador_dashboard'))
        # elif user.role == 'profissional':
        #     return redirect(url_for('profissional.dashboard'))

    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('main.index'))

# ==================================
# Rotas do Morador
# ==================================
@main.route('/morador_dashboard', methods=['GET', 'POST'])
@login_required
@permission_required('morador')
def morador_dashboard():
    form = AutorizarAcessoForm()
    
    if form.validate_on_submit():
        if not current_user.condominio_id:
            flash('Sua conta não está associada a um condomínio.', 'danger')
            return redirect(url_for('main.index'))
        
        morador_id = current_user.id
        condominio_id = current_user.condominio_id

        if criar_pre_autorizacao(morador_id, condominio_id, form.data):
            flash('Pré-autorização criada com sucesso!', 'success')
            return redirect(url_for('main.morador_dashboard'))
        else:
            flash('Erro ao criar a pré-autorização. Verifique os dados fornecidos.', 'danger')
            return redirect(url_for('main.morador_dashboard'))

    acessos_morador = get_acessos_morador(current_user.id)
    now = datetime.now()
    
    return render_template('morador/dashboard.html', form=form, acessos=acessos_morador, now=now)

# ==================================
# Rotas de Administrador
# ==================================
@main.route('/admin_dashboard')
@login_required
@permission_required('admin')
def admin_dashboard():
    users = get_all_users()
    condominios = get_all_condominios()
    
    now = datetime.now()
    return render_template('admin/dashboard.html', 
                           users=users, 
                           condominios=condominios,
                           csrf_token=generate_csrf(),
                           now=now)

@main.route('/admin_user_list')
@login_required
@permission_required('admin')
def admin_user_list():
    users = get_all_users()
    now = datetime.now()
    return render_template('admin/user_list.html', 
                           users=users, 
                           csrf_token=generate_csrf(),
                           now=now)

@main.route('/admin_condominio_list')
@login_required
@permission_required('admin')
def admin_condominio_list():
    condominios = get_all_condominios()
    now = datetime.now()
    return render_template('admin/condominio_list.html', 
                           condominios=condominios, 
                           csrf_token=generate_csrf(),
                           now=now)

@main.route('/admin/usuarios/novo', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_novo_usuario():
    form = UserForm()
    form.condominio_id.choices = [(-1, 'Nenhum')] + [(c.id, c.nome) for c in get_all_condominios()]

    if form.validate_on_submit():
        if create_user_admin(request.form):
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Erro ao criar usuário.', 'danger')
    
    now = datetime.now()
    return render_template('admin/novo_usuario.html', form=form, now=now)

@main.route('/admin/condominios/novo', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_novo_condominio():
    form = CondominioForm()
    form.plano_id.choices = [(-1, 'Nenhum')] + [(p.id, p.nome) for p in get_all_planos()]
    
    if form.validate_on_submit():
        if create_condominio_admin(request.form):
            flash('Condomínio criado com sucesso!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Erro ao criar condomínio.', 'danger')
    
    now = datetime.now()
    return render_template('admin/novo_condominio.html', form=form, now=now)

@main.route('/admin/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_editar_usuario(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    form = UserForm()
    form.condominio_id.choices = [(-1, 'Nenhum')] + [(c.id, c.nome) for c in get_all_condominios()]
    
    if request.method == 'GET':
        form.nome.data = user.nome
        form.email.data = user.email
        form.role.data = user.role
        form.apartamento.data = user.apartamento
        form.condominio_id.data = user.condominio_id if user.condominio_id else -1
        form.password.validators = []
    
    if form.validate_on_submit():
        if update_user_admin(user.id, request.form):
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Erro ao atualizar usuário.', 'danger')
            return redirect(url_for('main.admin_dashboard'))
    
    now = datetime.now()
    return render_template('admin/editar_usuario.html', form=form, user=user, now=now)

@main.route('/admin/usuarios/<int:user_id>/excluir', methods=['POST'])
@login_required
@permission_required('admin')
def admin_excluir_usuario(user_id):
    if delete_user_admin(user_id):
        flash('Usuário excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir usuário.', 'danger')
        
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/condominios/<int:condominio_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_editar_condominio(condominio_id):
    condominio = get_condominio_by_id(condominio_id)
    if not condominio:
        flash('Condomínio não encontrado.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    form = CondominioForm()
    form.plano_id.choices = [(-1, 'Nenhum')] + [(p.id, p.nome) for p in get_all_planos()]
    
    if request.method == 'GET':
        form.nome.data = condominio.nome
        form.endereco.data = condominio.endereco
        form.status_assinatura.data = condominio.status_assinatura
        form.plano_id.data = condominio.plano_id if condominio.plano_id else -1
    
    if form.validate_on_submit():
        if update_condominio_admin(condominio.id, request.form):
            flash('Condomínio atualizado com sucesso!', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Erro ao atualizar condomínio.', 'danger')
            return redirect(url_for('main.admin_dashboard'))
    
    now = datetime.now()
    return render_template('admin/editar_condominio.html', form=form, condominio=condominio, now=now)

@main.route('/admin/condominios/<int:condominio_id>/excluir', methods=['POST'])
@login_required
@permission_required('admin')
def admin_excluir_condominio(condominio_id):
    if delete_condominio_admin(condominio_id):
        flash('Condomínio excluído com sucesso!', 'success')
    else:
        flash('Erro ao excluir condomínio.', 'danger')
    
    return redirect(url_for('main.admin_dashboard'))

# ==================================
# Rotas de Planos
# ==================================
@main.route('/admin_planos_list')
@login_required
@permission_required('admin')
def admin_plano_list():
    planos = get_all_planos()
    return render_template('admin/plano_list.html', 
                           planos=planos, 
                           csrf_token=generate_csrf(),
                           )

@main.route('/admin/planos/<int:plano_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_editar_plano(plano_id):
    plano = Plano.query.get_or_404(plano_id)
    form = PlanoForm(obj=plano)

    if form.validate_on_submit():
        plano.nome = form.nome.data
        plano.valor_mensal = form.valor_mensal.data
        plano.dias_carencia = form.dias_carencia.data
        db.session.commit()
        flash('Plano atualizado com sucesso!', 'success')
        return redirect(url_for('main.admin_plano_list'))

    return render_template('admin/editar_plano.html', form=form, plano=plano)

@main.route('/admin/planos/<int:plano_id>/excluir', methods=['POST'])
@login_required
@permission_required('admin')
def admin_excluir_plano(plano_id):
    plano = Plano.query.get_or_404(plano_id)
    try:
        db.session.delete(plano)
        db.session.commit()
        flash('Plano excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir plano: {e}', 'danger')
        
    return redirect(url_for('main.admin_plano_list'))

@main.route('/admin/novo_plano', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_novo_plano():
    form = PlanoForm()
    if form.validate_on_submit():
        plano_existente = Plano.query.filter_by(nome=form.nome.data).first()
        if plano_existente:
            flash(f'O plano "{form.nome.data}" já existe. Por favor, escolha outro nome.', 'danger')
            return redirect(url_for('main.admin_novo_plano'))

        novo_plano = Plano(
            nome=form.nome.data,
            valor_mensal=form.valor_mensal.data,
            dias_carencia=form.dias_carencia.data
        )
        db.session.add(novo_plano)
        db.session.commit()
        flash('Plano de assinatura criado com sucesso!', 'success')
        return redirect(url_for('main.admin_plano_list'))
    
    now = datetime.now()
    return render_template('admin/novo_plano.html', form=form, now=now)

@main.route('/admin/alterar_plano/<int:condominio_id>', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_alterar_plano(condominio_id):
    condominio = Condominio.query.get_or_404(condominio_id)
    form = CondominioPlanoForm()
    
    form.plano_id.choices = [(plano.id, plano.nome) for plano in Plano.query.all()]
    
    if form.validate_on_submit():
        plano_selecionado = Plano.query.get(form.plano_id.data)
        if plano_selecionado:
            condominio.plano = plano_selecionado
            condominio.status_assinatura = 'ativo'

            if plano_selecionado.dias_carencia > 0:
                condominio.data_fim_carencia = datetime.utcnow() + timedelta(days=plano_selecionado.dias_carencia)
                condominio.status_assinatura = 'carencia'
            else:
                condominio.data_fim_carencia = None

            db.session.commit()
            flash('Plano do condomínio alterado com sucesso!', 'success')
            return redirect(url_for('main.admin_dashboard'))
    
    if condominio.plano:
        form.plano_id.data = condominio.plano.id
        
    now = datetime.now()
    return render_template('admin/alterar_plano.html', form=form, condominio=condominio, now=now)

@main.route('/api/condominio_tipo/<int:condominio_id>')
@login_required
@permission_required('sindico', 'admin')
def api_condominio_tipo(condominio_id):
    condominio = Condominio.query.get(condominio_id)
    if condominio:
        return jsonify({'tipo': condominio.tipo})
    return jsonify({'error': 'Condomínio não encontrado'}), 404

@main.route('/prestadores')
def prestadores():
    return render_template('prestadores.html')