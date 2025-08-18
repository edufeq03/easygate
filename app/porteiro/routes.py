# app/porteiro/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.decorators import permission_required
from app.models import Acesso, Profissional, db, Condominio, Portaria
from app.forms import (
    ProfissionalForm,
    RegistrarAcessoForm,
    EntradaManualForm
)
from app.services import (
    get_all_moradores_do_condominio,
    get_acessos_em_aberto,
    get_pre_autorizacoes_pendentes
)
from datetime import datetime
import re
from app import socketio

# Definição do Blueprint do Porteiro
porteiro = Blueprint('porteiro', __name__, url_prefix='/porteiro', template_folder='templates')

# ==============================================================================
# Rotas do Painel Principal
# ==============================================================================

@porteiro.route('/dashboard')
@login_required
@permission_required('porteiro')
def dashboard():
    # O porteiro agora está ligado a uma portaria, que está ligada a um condomínio
    if not current_user.portaria:
        flash('Sua conta não está associada a uma portaria.', 'danger')
        return redirect(url_for('main.index'))
    # Usa o ID da portaria do usuário para buscar os acessos
    portaria_id = current_user.portaria.id
    condominio_id = current_user.portaria.condominio.id

    if not condominio_id:
        flash('Sua conta não está associada a um condomínio.', 'danger')
        return redirect(url_for('main.index'))
    
    pre_autorizacoes_pendentes = get_pre_autorizacoes_pendentes(condominio_id)
    acessos_em_aberto = get_acessos_em_aberto(condominio_id)
    
    # Busca por solicitações de entrada por QR Code
    solicitacoes_qr_code = Acesso.query.filter_by(
        condominio_id=condominio_id,
        status='pendente'
    ).all()
    
    return render_template('dashboard.html',
                           pre_autorizacoes_pendentes=pre_autorizacoes_pendentes,
                           acessos_em_aberto=acessos_em_aberto,
                           solicitacoes_qr_code=solicitacoes_qr_code)

# ==============================================================================
# Rotas de Profissional
# ==============================================================================

@porteiro.route('/cadastrar_profissional')
@login_required
@permission_required('porteiro')
def form_cadastrar_profissional():
    form = ProfissionalForm()
    now = datetime.now()
    return render_template('cadastrar_profissional.html', form=form, now=now)

@porteiro.route('/cadastrar_profissional', methods=['POST'])
@login_required
@permission_required('porteiro')
def cadastrar_profissional():
    form = ProfissionalForm()
    if form.validate_on_submit():
        profissionais_existentes = Profissional.query.filter_by(
            nome=form.nome.data
        ).all()

        if profissionais_existentes:
            flash(f'Atenção: Já existem {len(profissionais_existentes)} profissionais cadastrados com o nome "{form.nome.data}". Verifique se é a mesma pessoa antes de continuar.', 'warning')
        
        try:
            foto_url = None
            if form.foto.data:
                pass

            novo_profissional = Profissional(
                nome=form.nome.data,
                placa_veiculo=form.placa_veiculo.data,
                empresa=form.empresa.data,
                url_foto=foto_url
            )
            
            db.session.add(novo_profissional)
            db.session.commit()
            
            flash(f'Profissional "{novo_profissional.nome}" cadastrado com sucesso!', 'success')
            return redirect(url_for('porteiro.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar profissional: {e}', 'danger')
            return redirect(url_for('porteiro.dashboard'))
    
    flash('Erro no formulário. Verifique os dados.', 'danger')
    return redirect(url_for('porteiro.form_cadastrar_profissional'))

@porteiro.route('/consultar_profissional')
@login_required
@permission_required('porteiro')
def consultar_profissional():
    query = request.args.get('query', '').strip()
    acesso_id = request.args.get('acesso_id', type=int)
    profissionais_encontrados = []
    
    if query:
        profissionais_encontrados = Profissional.query.filter(
            (Profissional.nome.ilike(f'%{query}%')) |
            (Profissional.placa_veiculo.ilike(f'%{query}%'))
        ).all()
        
        if not profissionais_encontrados:
            flash('Profissional não encontrado.', 'info')

    form_cadastro = ProfissionalForm(nome=query)
    moradores_condominio = get_all_moradores_do_condominio(current_user.condominio_id)
    form_acesso_direto = RegistrarAcessoForm()
    form_acesso_direto.morador_id.choices = [
        (m.id, f"{m.nome} (Apto: {m.apartamento})") for m in moradores_condominio
    ]
    
    now = datetime.now()
    return render_template(
        'consulta_resultados.html', 
        query=query, 
        profissionais_encontrados=profissionais_encontrados,
        acesso_id=acesso_id,
        form_cadastro=form_cadastro,
        form_acesso_direto=form_acesso_direto,
        moradores_condominio=moradores_condominio,
        now=now
    )

# ==============================================================================
# Rotas de Acesso (Entrada e Saída)
# ==============================================================================

@porteiro.route('/registrar_acesso_direto', methods=['POST'])
@login_required
@permission_required('porteiro')
def registrar_acesso_direto():
    profissional_id = request.form.get('profissional_id', type=int)
    morador_id = request.form.get('morador_id', type=int)
    servico = request.form.get('servico')

    if not profissional_id or not morador_id or not servico:
        flash('Por favor, preencha todos os campos para registrar o acesso.', 'danger')
        return redirect(url_for('porteiro.consultar_profissional'))

    novo_acesso = Acesso(
        profissional_id=profissional_id,
        usuario_morador_id=morador_id,
        usuario_porteiro_id=current_user.id,
        condominio_id=current_user.condominio_id,
        data_acesso=datetime.now(),
        status='em_andamento',
        servico=servico
    )
    db.session.add(novo_acesso)
    db.session.commit()

    flash(f'Entrada de {Profissional.query.get(profissional_id).nome} registrada com sucesso!', 'success')
    return redirect(url_for('porteiro.dashboard'))

@porteiro.route('/registrar_entrada_manual/<int:acesso_id>')
@login_required
@permission_required('porteiro')
def registrar_entrada_manual(acesso_id):
    acesso = Acesso.query.get_or_404(acesso_id)

    if acesso.status == 'pendente':
        try:
            acesso.status = 'em_andamento'
            acesso.data_acesso = datetime.now()
            acesso.usuario_porteiro_id = current_user.id
            db.session.commit()
            flash(f'Entrada de {acesso.profissional.nome if acesso.profissional else acesso.empresa} registrada com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar entrada: {e}', 'danger')
    else:
        flash('Este acesso não está pendente e não pode ser autorizado.', 'warning')
    
    return redirect(url_for('porteiro.dashboard'))

@porteiro.route('/registrar_saida/<int:acesso_id>', methods=['POST'])
@login_required
@permission_required('porteiro')
def registrar_saida(acesso_id):
    acesso = Acesso.query.get(acesso_id)

    if not acesso or acesso.status == 'finalizado':
        flash('Erro: Acesso não encontrado ou já foi finalizado.', 'danger')
        return redirect(url_for('porteiro.dashboard'))

    acesso.data_saida = datetime.now()
    acesso.status = 'finalizado'
    acesso.porteiro_saida_id = current_user.id
    db.session.commit()

    if acesso.profissional:
        nome_profissional = acesso.profissional.nome
    else:
        nome_profissional = 'Profissional não identificado'
    
    flash(f'Saída de {nome_profissional} registrada com sucesso!', 'success')
    return redirect(url_for('porteiro.dashboard'))

# ==============================================================================
# Rotas de Acesso (Entrada e Saída)
# ==============================================================================


@porteiro.route('/solicitacao_acesso_profissional_qrcode/<int:portaria_id>/<int:profissional_id>', methods=['POST'])
#@login_required
#@permission_required('porteiro')
def solicitacao_acesso_profissional_qrcode(portaria_id, profissional_id):
    # Verifica a existência da portaria
    portaria = Portaria.query.get_or_404(portaria_id)
    
    # Verifica a existência do profissional (agora global)
    profissional = Profissional.query.get_or_404(profissional_id)
    
    # O ID do condomínio é obtido da portaria
    condominio_id = portaria.condominio_id

    nova_solicitacao = Acesso(
        condominio_id=condominio_id,
        profissional_id=profissional.id,
        portaria_id=portaria_id, # Novo campo
        data_acesso=datetime.now(),
        status='pendente',
        tipo_acesso='qrcode'
    )
    db.session.add(nova_solicitacao)
    
    try:
        db.session.commit()
        
        data_para_enviar = {
            'id': nova_solicitacao.id,
            'profissional_nome': profissional.nome,
            'horario': nova_solicitacao.data_acesso.strftime('%H:%M:%S')
        }
        
        # AQUI É O PONTO CHAVE: Emitir para a sala da portaria, não do condomínio
        room_name = f'porteiro_dashboard_{portaria_id}'
        print(f"Emitindo evento 'nova_solicitacao_acesso' para a sala: {room_name}")
        socketio.emit(
            'nova_solicitacao_acesso',
            data_para_enviar,
            room=room_name
        )
        return jsonify({'mensagem': 'Solicitação de acesso enviada com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao emitir notificação SocketIO ou ao salvar no DB: {e}")
        return jsonify({'mensagem': f'Erro ao processar solicitação: {e}'}), 500
