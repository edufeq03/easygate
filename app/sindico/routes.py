# app/sindico/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from app.models import db, Portaria, User
from app.decorators import permission_required, sindico_required
from app.forms import RelatorioAcessoForm, PortariaForm
from app.sindico.forms import UserForm, MoradorForm
from app.services import (
    get_condominio_info,
    get_ultimas_movimentacoes_do_dia,
    get_pre_autorizacoes_pendentes,
    calcular_tempo_economizado,
    calcular_tempo_economizado_total,
    contar_moradores_condominio,
    contar_profissionais_condominio,
    get_acessos_em_andamento,
    get_all_moradores_do_condominio,
    get_relatorio_acessos
)
from datetime import datetime

# ==============================================================================
# Define o Blueprint para as rotas do síndico
# O nome 'sindico' deve ser consistente com o registro em __init__.py
# ==============================================================================
sindico = Blueprint('sindico', __name__, url_prefix='/sindico', template_folder='templates')


# ==================================
# Rotas do Síndico (sindico Blueprint)
# ==================================
@sindico.route('/dashboard')
@login_required
@permission_required('sindico')
def sindico_dashboard():
    sindico_info = current_user
    condominio = get_condominio_info(sindico_info.condominio_id)
    
    ultimas_movimentacoes = get_ultimas_movimentacoes_do_dia(condominio.id, limite=10)
    acessos_pendentes = get_pre_autorizacoes_pendentes(condominio.id)
    tempo_economizado_mes = calcular_tempo_economizado(condominio.id)
    tempo_economizado_total = calcular_tempo_economizado_total(condominio.id)
    total_moradores = contar_moradores_condominio(condominio.id)
    total_profissionais = contar_profissionais_condominio(condominio.id)
    acessos_em_andamento = get_acessos_em_andamento(condominio.id)
    
    return render_template('dashboard.html',
                           sindico=sindico_info,
                           condominio=condominio,
                           ultimas_movimentacoes=ultimas_movimentacoes,
                           acessos_pendentes=len(acessos_pendentes),
                           tempo_economizado_mes=tempo_economizado_mes,
                           tempo_economizado_total=tempo_economizado_total,
                           total_moradores=total_moradores,
                           total_profissionais=total_profissionais,
                           acessos_em_andamento=acessos_em_andamento)

@sindico.route('/relatorios', methods=['GET', 'POST'])
@login_required
@permission_required('sindico')
def relatorios():
    form = RelatorioAcessoForm()
    relatorio_gerado = None

    if form.validate_on_submit():
        data_inicio = form.data_inicio.data
        data_fim = form.data_fim.data
        condominio_id = current_user.condominio_id
        relatorio_gerado = get_relatorio_acessos(condominio_id, data_inicio, data_fim)

    now = datetime.now()
    return render_template('sindico/relatorios.html',
                           form=form,
                           relatorio=relatorio_gerado,
                           now=now)


# Rotas do CRUD de Portarias
@sindico.route('/portarias')
@login_required
@permission_required('sindico')
def listar_portarias():
    condominio_id = current_user.condominio_id
    portarias = Portaria.query.filter_by(condominio_id=condominio_id).order_by(Portaria.nome).all()
    return render_template('sindico/portaria_list.html', portarias=portarias)

@sindico.route('/portarias/novo', methods=['GET', 'POST'])
@login_required
@permission_required('sindico')
def nova_portaria():
    form = PortariaForm()
    if form.validate_on_submit():
        nome = form.nome.data
        condominio_id = current_user.condominio_id
        
        nova_portaria = Portaria(
            nome=nome,
            condominio_id=condominio_id
        )
        db.session.add(nova_portaria)
        db.session.commit()
        flash('Portaria criada com sucesso!', 'success')
        return redirect(url_for('sindico.listar_portarias'))
    
    return render_template('sindico/portaria_form.html', form=form, title='Nova Portaria')

@sindico.route('/portarias/<int:portaria_id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('sindico')
def editar_portaria(portaria_id):
    portaria = Portaria.query.get_or_404(portaria_id)
    # Apenas o síndico do condomínio pode editar sua portaria
    if portaria.condominio_id != current_user.condominio_id:
        flash('Você não tem permissão para editar esta portaria.', 'danger')
        return redirect(url_for('sindico.listar_portarias'))

    form = PortariaForm(obj=portaria)
    if form.validate_on_submit():
        portaria.nome = form.nome.data
        db.session.commit()
        flash('Portaria atualizada com sucesso!', 'success')
        return redirect(url_for('sindico.listar_portarias'))
    
    return render_template('sindico/portaria_form.html', form=form, title='Editar Portaria')

@sindico.route('/portarias/<int:portaria_id>/excluir', methods=['POST'])
@login_required
@permission_required('sindico')
def excluir_portaria(portaria_id):
    portaria = Portaria.query.get_or_404(portaria_id)
    if portaria.condominio_id != current_user.condominio_id:
        flash('Você não tem permissão para excluir esta portaria.', 'danger')
        return redirect(url_for('sindico.listar_portarias'))
        
    try:
        db.session.delete(portaria)
        db.session.commit()
        flash('Portaria excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir portaria: {e}', 'danger')

    return redirect(url_for('sindico.listar_portarias'))

# Rota para gerar o QR Code (API ou rota de visualização)
@sindico.route('/portarias/<int:portaria_id>/qrcode')
@login_required
@permission_required('sindico')
def gerar_qrcode_portaria(portaria_id):
    portaria = Portaria.query.get_or_404(portaria_id)
    if portaria.condominio_id != current_user.condominio_id:
        flash('Você não tem permissão para esta portaria.', 'danger')
        return redirect(url_for('sindico.listar_portarias'))
        
    # Aqui você irá gerar o conteúdo do QR Code.
    # Por exemplo, a URL que o porteiro irá acessar.
    # URL de exemplo: https://easygate.com/api/portaria/1
    # O conteúdo do QR code deve ser único para cada portaria.
    qr_code_content = f"https://easygate.com/api/portaria/{portaria.id}"
    portaria.qr_code_portaria = qr_code_content
    db.session.commit()
    flash('QR Code gerado e salvo com sucesso!', 'success')
    
    return redirect(url_for('sindico.listar_portarias'))

# ==============================================================================
# Rotas para Gerenciar Porteiros (CRUD)
# ==============================================================================

@sindico.route('/porteiros')
@login_required
@sindico_required
def listar_porteiros():
    """Rota para listar todos os porteiros do condomínio do síndico."""
    # Filtra usuários com role 'porteiro' e pertencentes ao condomínio do síndico
    # O user atual logado é o sindico, logo é possível obter seu condomínio
    if current_user.condominio_id:
        porteiros = User.query.filter_by(
            role='porteiro', 
            condominio_id=current_user.condominio_id
        ).all()
        return render_template(
            'sindico/listar_porteiros.html', 
            porteiros=porteiros, 
            titulo='Lista de Porteiros'
        )
    return redirect(url_for('main.index'))

@sindico.route('/porteiros/adicionar', methods=['GET', 'POST'])
@login_required
@sindico_required
def adicionar_porteiro():
    """Rota para adicionar um novo porteiro."""
    form = UserForm()
    
    # IMPORTANTE: Popule os choices ANTES da validação
    form.portaria.choices = [(p.id, p.nome) for p in Portaria.query.filter_by(condominio_id=current_user.condominio_id).all()]
    
    if form.validate_on_submit():
        # A validação da senha deve ser tratada diretamente no formulário.
        # Se você tiver um DataRequired, este bloco de 'if not' não é mais necessário.
    
        novo_porteiro = User(
            nome=form.nome.data,
            email=form.email.data,
            role='porteiro',
            condominio_id=current_user.condominio_id,
            portaria_id=form.portaria.data
        )
        novo_porteiro.set_senha(form.senha.data)
        db.session.add(novo_porteiro)
        db.session.commit()
        
        flash('Porteiro adicionado com sucesso!')
        return redirect(url_for('sindico.listar_porteiros'))
    
    # Se a validação falhou (GET ou POST com erro), o formulário é renderizado.
    # Os erros serão exibidos pelo template, já que você removeu o Flask-Bootstrap.
    return render_template(
        'sindico/form_porteiro.html', 
        form=form, 
        titulo='Adicionar Porteiro'
    )

@sindico.route('/porteiros/editar/<int:porteiro_id>', methods=['GET', 'POST'])
@login_required
@sindico_required
def editar_porteiro(porteiro_id):
    """Rota para editar um porteiro existente."""
    porteiro = User.query.get_or_404(porteiro_id)
    # Valida se o porteiro pertence ao condomínio do síndico
    if porteiro.condominio_id != current_user.condominio_id:
        flash('Você não tem permissão para editar este porteiro.', 'danger')
        return redirect(url_for('sindico.listar_porteiros'))

    form = UserForm(obj=porteiro)
    if form.validate_on_submit():
        porteiro.nome = form.nome.data
        porteiro.email = form.email.data
        # A senha é opcional na edição
        if form.senha.data:
            porteiro.set_senha(form.senha.data)
        porteiro.portaria_id = form.portaria.data
        db.session.commit()
        flash('Porteiro atualizado com sucesso!')
        return redirect(url_for('sindico.listar_porteiros'))
    
    # Preenche o formulário com os dados do porteiro
    form.portaria.choices = [(p.id, p.nome) for p in Portaria.query.filter_by(condominio_id=current_user.condominio_id).all()]
    return render_template(
        'sindico/form_porteiro.html', 
        form=form, 
        titulo='Editar Porteiro'
    )

@sindico.route('/porteiros/excluir/<int:porteiro_id>', methods=['POST'])
@login_required
@sindico_required
def excluir_porteiro(porteiro_id):
    """Rota para excluir um porteiro."""
    porteiro = User.query.get_or_404(porteiro_id)
    # Valida se o porteiro pertence ao condomínio do síndico
    if porteiro.condominio_id != current_user.condominio_id:
        flash('Você não tem permissão para excluir este porteiro.', 'danger')
        return redirect(url_for('sindico.listar_porteiros'))

    db.session.delete(porteiro)
    db.session.commit()
    flash('Porteiro excluído com sucesso!')
    return redirect(url_for('sindico.listar_porteiros'))

@sindico.route('/moradores/adicionar', methods=['GET', 'POST'])
@login_required
@sindico_required
def adicionar_morador():
    """Rota para adicionar um novo morador."""
    form = MoradorForm()
    
    if form.validate_on_submit():
        novo_morador = User(
            nome=form.nome.data,
            email=form.email.data,
            role='morador',  # Define o papel como 'morador'
            apartamento=form.apartamento.data,
            condominio_id=current_user.condominio_id
        )
        novo_morador.set_senha(form.senha.data)
        db.session.add(novo_morador)
        db.session.commit()
        
        flash('Morador adicionado com sucesso!')
        return redirect(url_for('sindico.sindico_listar_moradores'))
    
    return render_template(
        'sindico/form_morador.html', 
        form=form, 
        titulo='Adicionar Morador'
    )

# Rota para síndico listar moradores
@sindico.route('/moradores')
@login_required
@sindico_required
def sindico_listar_moradores():
    """Exibe uma lista de todos os moradores do condomínio do síndico."""
    moradores = User.query.filter_by(role='morador', condominio_id=current_user.condominio_id).all()
    return render_template('sindico/listar_moradores.html', 
                           moradores=moradores, 
                           titulo='Listagem de Moradores')