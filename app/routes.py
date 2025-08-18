# app/routes.py
from flask import render_template, redirect, url_for, flash, Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import generate_csrf
from datetime import datetime, timedelta # Importação do datetime
import re
from app.decorators import permission_required
from app.models import User, Condominio, db, Acesso, Profissional, Plano
from app.forms import (
    LoginForm,
    RelatorioAcessoForm,
    AutorizarAcessoForm,
    UserForm,
    CondominioForm,
    ProfissionalForm,
    RegistrarAcessoForm,
    EntradaManualForm,
    PlanoForm,
    CondominioPlanoForm
)
from app.services import (
    get_pre_autorizacoes_pendentes,
    get_acessos_em_aberto,
    get_condominio_info,
    get_ultimas_movimentacoes_do_dia,
    get_relatorio_acessos,
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
    get_all_moradores_do_condominio,
    calcular_tempo_economizado,
    calcular_tempo_economizado_total,
    contar_moradores_condominio,
    contar_profissionais_condominio,
    get_acessos_em_andamento
)
from wtforms.validators import DataRequired

# Cria uma instância de Blueprint
main = Blueprint('main', __name__)

# ==================================
# Rotas de Autenticação
# ==================================

@main.route('/')
@main.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif current_user.role == 'sindico':
            return redirect(url_for('main.sindico_dashboard'))
        elif current_user.role == 'porteiro':
            return redirect(url_for('porteiro.dashboard'))
        elif current_user.role == 'morador':
            return redirect(url_for('main.morador_dashboard'))
        elif current_user.role == 'profissional':
            return redirect(url_for('profissional.dashboard'))
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
        
        # Redirecionamento após o login
        if user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif user.role == 'sindico':
            return redirect(url_for('main.sindico_dashboard'))
        elif user.role == 'porteiro':
            return redirect(url_for('porteiro.dashboard'))
        elif user.role == 'morador':
            return redirect(url_for('main.morador_dashboard'))
        elif user.role == 'profissional':
            return redirect(url_for('profissional.dashboard'))

    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('main.index'))

# ==================================
# Rotas do Síndico
# ==================================
@main.route('/sindico_dashboard')
@login_required
@permission_required('sindico')
def sindico_dashboard():
    # 1. Obter informações do síndico e do condomínio
    sindico_info = current_user
    condominio = get_condominio_info(sindico_info.condominio_id)
    
    # 2. Usa a função do services.py para obter as últimas movimentações
    ultimas_movimentacoes = get_ultimas_movimentacoes_do_dia(condominio.id, limite=10)
    
    # 3. Usa a função do services.py para contar os acessos pendentes
    acessos_pendentes = get_pre_autorizacoes_pendentes(condominio.id)

    # 4. Obtém os dados que estavam faltando para os cartões
    tempo_economizado_mes = calcular_tempo_economizado(condominio.id)
    tempo_economizado_total = calcular_tempo_economizado_total(condominio.id)
    total_moradores = contar_moradores_condominio(condominio.id)
    total_profissionais = contar_profissionais_condominio(condominio.id)
    acessos_em_andamento = get_acessos_em_andamento(condominio.id)
    
    return render_template('sindico/dashboard.html',
                           sindico=sindico_info,
                           condominio=condominio,
                           ultimas_movimentacoes=ultimas_movimentacoes,
                           acessos_pendentes=len(acessos_pendentes),
                           tempo_economizado_mes=tempo_economizado_mes,
                           tempo_economizado_total=tempo_economizado_total,
                           total_moradores=total_moradores,
                           total_profissionais=total_profissionais,
                           acessos_em_andamento=acessos_em_andamento)

# SINDICO LISTAR MORADORES
@main.route('/sindico_listar_moradores')
@login_required
@permission_required('sindico')
def sindico_listar_moradores():
    """
    Rota para listar e gerenciar moradores do condomínio do síndico.
    """
    condominio_id = current_user.condominio_id
    if not condominio_id:
        flash('Você não está associado a um condomínio.', 'danger')
        return redirect(url_for('main.sindico_dashboard'))

    moradores = get_all_moradores_do_condominio(condominio_id)
    return render_template('sindico/listar_moradores.html',
                           moradores=moradores,
                           csrf_token=generate_csrf())


@main.route('/sindico/relatorios', methods=['GET', 'POST'])
@login_required
@permission_required('sindico')
def relatorios():
    form = RelatorioAcessoForm()
    relatorio_gerado = None

    if form.validate_on_submit():
        data_inicio = form.data_inicio.data
        data_fim = form.data_fim.data
        condominio_id = current_user.condominio_id
        
        # Chama a função do services.py para gerar o relatório
        relatorio_gerado = get_relatorio_acessos(condominio_id, data_inicio, data_fim)

    now = datetime.now()
    return render_template('sindico/relatorios.html',
                           form=form,
                           relatorio=relatorio_gerado,
                           now=now)

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

        # Usa a função do services.py para criar a pré-autorização
        if criar_pre_autorizacao(morador_id, condominio_id, form.data):
            flash('Pré-autorização criada com sucesso!', 'success')
            return redirect(url_for('main.morador_dashboard'))
        else:
            flash('Erro ao criar a pré-autorização. Verifique os dados fornecidos.', 'danger')
            return redirect(url_for('main.morador_dashboard'))

    # Usa a função do services.py para buscar os acessos do morador
    acessos_morador = get_acessos_morador(current_user.id)
    now = datetime.now()
    
    # Renderiza o template, passando o formulário e os acessos
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

# LISTAR PLANO
@main.route('/admin_planos_list')
@login_required
@permission_required('admin')
def admin_plano_list():
    """
    Rota para listar todos os planos de assinatura.
    Apenas usuários com perfil 'admin' podem acessá-la.
    """
    planos = get_all_planos()
    return render_template('admin/plano_list.html', 
                           planos=planos, 
                           csrf_token=generate_csrf(),
                           )

# EDITAR PLANO - CRUD de planos.
@main.route('/admin/planos/<int:plano_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_editar_plano(plano_id):
    """
    Rota para editar um plano de assinatura existente.
    """
    plano = Plano.query.get_or_404(plano_id)
    form = PlanoForm(obj=plano) # Pré-popula o formulário com os dados do plano

    if form.validate_on_submit():
        plano.nome = form.nome.data
        plano.valor_mensal = form.valor_mensal.data
        plano.dias_carencia = form.dias_carencia.data
        db.session.commit()
        flash('Plano atualizado com sucesso!', 'success')
        return redirect(url_for('main.admin_plano_list'))

    return render_template('admin/editar_plano.html', form=form, plano=plano)

# EXCLUIR PLANO
@main.route('/admin/planos/<int:plano_id>/excluir', methods=['POST'])
@login_required
@permission_required('admin')
def admin_excluir_plano(plano_id):
    """
    Rota para excluir um plano de assinatura.
    """
    plano = Plano.query.get_or_404(plano_id)
    try:
        db.session.delete(plano)
        db.session.commit()
        flash('Plano excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir plano: {e}', 'danger')
        
    return redirect(url_for('main.admin_plano_list'))

# CRIAR PLANO
@main.route('/admin/novo_plano', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_novo_plano():
    form = PlanoForm()
    if form.validate_on_submit():
        # LÓGICA CORRIGIDA: Verifica se o plano já existe antes de criar
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

# ALTERAR PLANO DO CONDOMINIO
@main.route('/admin/alterar_plano/<int:condominio_id>', methods=['GET', 'POST'])
@login_required
@permission_required('admin')
def admin_alterar_plano(condominio_id):
    condominio = Condominio.query.get_or_404(condominio_id)
    form = CondominioPlanoForm()
    
    # Popula a lista de opções do campo 'plano_id' com os planos do banco de dados
    form.plano_id.choices = [(plano.id, plano.nome) for plano in Plano.query.all()]
    
    if form.validate_on_submit():
        # Busca o plano selecionado e atualiza o condomínio
        plano_selecionado = Plano.query.get(form.plano_id.data)
        if plano_selecionado:
            condominio.plano = plano_selecionado
            condominio.status_assinatura = 'ativo' # Ou 'carencia', dependendo da sua lógica

            # Opcional: Recalcula a data de carência se o plano tiver dias de carência
            if plano_selecionado.dias_carencia > 0:
                condominio.data_fim_carencia = datetime.utcnow() + timedelta(days=plano_selecionado.dias_carencia)
                condominio.status_assinatura = 'carencia'
            else:
                condominio.data_fim_carencia = None

            db.session.commit()
            flash('Plano do condomínio alterado com sucesso!', 'success')
            return redirect(url_for('main.admin_dashboard'))
    
    # Se for GET, pré-seleciona o plano atual do condomínio no formulário
    if condominio.plano:
        form.plano_id.data = condominio.plano.id
        
    now = datetime.now()
    return render_template('admin/alterar_plano.html', form=form, condominio=condominio, now=now)

# Rota para identificar o tipo do condominio
@main.route('/api/condominio_tipo/<int:condominio_id>')
@login_required
@permission_required('sindico', 'admin') # Rotas de API também devem ser seguras
def api_condominio_tipo(condominio_id):
    condominio = Condominio.query.get(condominio_id)
    if condominio:
        return jsonify({'tipo': condominio.tipo})
    return jsonify({'error': 'Condomínio não encontrado'}), 404