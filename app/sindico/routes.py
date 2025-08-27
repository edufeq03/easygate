# app/sindico/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from app.models import db, Portaria
from app.decorators import permission_required
from app.forms import RelatorioAcessoForm, PortariaForm
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

@sindico.route('/listar-moradores')
@login_required
@permission_required('sindico')
def sindico_listar_moradores():
    condominio_id = current_user.condominio_id
    if not condominio_id:
        flash('Você não está associado a um condomínio.', 'danger')
        return redirect(url_for('sindico.sindico_dashboard'))

    moradores = get_all_moradores_do_condominio(condominio_id)
    return render_template('sindico/listar_moradores.html',
                           moradores=moradores,
                           csrf_token=generate_csrf())


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
