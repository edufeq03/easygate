# app/porteiro/routes.py

# Este arquivo define as rotas e a lógica para o Blueprint do porteiro.

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.forms import (
    RegistrarAcessoForm,
    EntradaManualForm,
)
from app.services import (
    get_pre_autorizacoes_pendentes,
    get_acessos_em_andamento,
    get_total_acessos_hoje,
    get_ultimos_acessos_hoje,
    registrar_entrada_acesso_autorizado,
    registrar_saida_acesso,
    buscar_profissional_por_cpf,
    criar_profissional_acesso_imediato
)

# Cria o Blueprint do Porteiro com o prefixo de URL
porteiro = Blueprint('porteiro', __name__, url_prefix='/porteiro', template_folder='templates')

@porteiro.route('/dashboard')
@login_required
@permission_required('porteiro')
def porteiro_dashboard():
    acessos_em_andamento = get_acessos_em_andamento(current_user.condominio_id) 
    pre_autorizacoes_pendentes = get_pre_autorizacoes_pendentes(current_user.condominio_id)
    total_acessos = get_total_acessos_hoje(current_user.condominio_id)
    ultimos_acessos = get_ultimos_acessos_hoje(current_user.condominio_id)
    
    # CORREÇÃO: Usar o nome do arquivo HTML diretamente.
    return render_template('dashboard_porteiro.html', 
                           acessos_em_andamento=acessos_em_andamento,
                           pre_autorizacoes_pendentes=pre_autorizacoes_pendentes,
                           total_acessos=total_acessos,
                           ultimos_acessos=ultimos_acessos)

@porteiro.route('/autorizar-acesso/<int:acesso_id>', methods=['POST'])
@login_required
@permission_required('porteiro')
def autorizar_acesso(acesso_id):
    if registrar_entrada_acesso_autorizado(acesso_id, current_user.id):
        flash('Acesso autorizado com sucesso!', 'success')
    else:
        flash('Erro ao autorizar acesso. Tente novamente.', 'danger')
        
    # CORREÇÃO: O endpoint correto é o nome da função que renderiza o dashboard.
    return redirect(url_for('porteiro.porteiro_dashboard'))

@porteiro.route('/registrar-saida/<int:acesso_id>', methods=['POST'])
@login_required
@permission_required('porteiro')
def registrar_saida(acesso_id):
    if registrar_saida_acesso(acesso_id, current_user.id):
        flash('Saída registrada com sucesso!', 'success')
    else:
        flash('Erro ao registrar saída. O acesso pode já ter sido finalizado.', 'danger')
        
    # CORREÇÃO: O endpoint correto é o nome da função que renderiza o dashboard.
    return redirect(url_for('porteiro.porteiro_dashboard'))

@porteiro.route('/acesso-imediato', methods=['GET', 'POST'])
@login_required
@permission_required('porteiro')
def acesso_imediato():
    form_buscar = RegistrarAcessoForm()
    form_entrada = EntradaManualForm()
    
    profissional = None
    if form_buscar.validate_on_submit():
        profissional = buscar_profissional_por_cpf(form_buscar.cpf.data)
        if not profissional:
            flash('Profissional não encontrado. Preencha o formulário para cadastrá-lo e registrar o acesso.', 'warning')
    
    if form_entrada.validate_on_submit():
        if criar_profissional_acesso_imediato(
            form_entrada.nome_profissional.data,
            form_entrada.servico_profissional.data,
            form_entrada.empresa_profissional.data,
            form_entrada.apartamento.data,
            current_user.id
        ):
            flash('Acesso imediato registrado com sucesso!', 'success')
        else:
            flash('Erro ao registrar acesso imediato.', 'danger')
        # CORREÇÃO: O endpoint correto é o nome da função que renderiza o dashboard.
        return redirect(url_for('porteiro.porteiro_dashboard'))
            
    # CORREÇÃO: Usar o nome do arquivo HTML diretamente.
    return render_template(
        'acesso_imediato.html',
        form_buscar=form_buscar,
        form_entrada=form_entrada,
        profissional=profissional
    )