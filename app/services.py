# app/services.py
# Este arquivo contém as principais funções de lógica de negócio do sistema.
# O objetivo é separar a lógica das rotas do Flask para manter o código mais limpo.

from app.models import Acesso, Profissional, User, Condominio, Plano, db
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
from sqlalchemy import func

# --- Funções para Moradores ---

def criar_pre_autorizacao(morador_id, condominio_id, form_data):
    """
    Cria uma pré-autorização de acesso com os dados fornecidos pelo morador.
    O morador não precisa informar dados do profissional.
    """
    try:
        pre_autorizacao = Acesso(
            condominio_id=condominio_id,
            usuario_morador_id=morador_id,
            data_prevista_acesso=form_data.get('data_prevista_acesso'),
            servico=form_data.get('servico'),
            empresa=form_data.get('empresa'),
            observacoes_morador=form_data.get('observacoes_morador'),
            status='pendente'
        )
        db.session.add(pre_autorizacao)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        # Log do erro para depuração
        print(f"Erro ao criar pré-autorização: {e}")
        return False

def get_acessos_morador(morador_id):
    """
    Busca o histórico de acessos para um morador específico.
    A consulta faz um join com a tabela de Profissional para obter o nome.
    """
    # A consulta foi corrigida para usar o relationship morador para evitar ambiguidade.
    # O query.join(Acesso.profissional) usa o relationship definido no models.py
    return db.session.query(Acesso)\
             .filter(Acesso.usuario_morador_id == morador_id)\
             .order_by(Acesso.data_prevista_acesso.desc())\
             .limit(8)\
             .all()


# --- Funções para Porteiros ---

def get_pre_autorizacoes_pendentes(condominio_id):
    """
    Busca todas as pré-autorizações pendentes para um condomínio específico.
    Retorna objetos Acesso completos, prontos para uso no template.
    """
    return Acesso.query.filter_by(
        condominio_id=condominio_id,
        status='pendente'
    ).order_by(Acesso.data_prevista_acesso).all()

def registrar_entrada_acesso_autorizado(acesso_id, porteiro_id):
    """
    Atualiza uma pré-autorização para o status 'autorizado'.
    """
    acesso = Acesso.query.get(acesso_id)
    if acesso:
        acesso.status = 'autorizado'
        acesso.usuario_porteiro_id = porteiro_id
        acesso.data_acesso = datetime.now()
        db.session.commit()
        return True
    return False

def get_acessos_em_aberto(condominio_id):
    """
    Busca todos os acessos que foram registrados e ainda não foram finalizados.
    """
    return Acesso.query.filter_by(
        condominio_id=condominio_id,
        status='em_andamento'
    ).order_by(Acesso.data_acesso.desc()).all()

def registrar_saida_acesso(acesso_id, porteiro_id):
    """
    Finaliza um acesso registrando a data de saída.
    """
    acesso = Acesso.query.get(acesso_id)
    if acesso and acesso.status == 'autorizado':
        acesso.status = 'finalizado'
        acesso.data_saida = datetime.now()
        db.session.commit()
        return True
    return False

def buscar_profissional_por_cpf(cpf):
    """
    Busca um profissional pelo CPF.
    """
    return Profissional.query.filter_by(cpf=cpf).first()

def criar_profissional_acesso_imediato(nome, servico, empresa, morador, porteiro):
    """
    Cria um novo profissional e um acesso imediato sem pré-autorização.
    """
    # A lógica complexa para encontrar o morador e inserir os dados virá aqui.
    pass


# --- Funções para Síndicos ---

def get_condominio_info(condominio_id):
    """
    Busca as informações básicas de um condomínio pelo ID.
    """
    return Condominio.query.filter_by(id=condominio_id).first()

def get_ultimas_movimentacoes_do_dia(condominio_id, limite=10):
    """
    Busca as últimas entradas e saídas do dia para um condomínio específico.
    """
    hoje = date.today()
    return db.session.query(
        Acesso.data_acesso,
        Acesso.data_saida,
        Profissional.nome,
        User.nome.label('morador_nome'),
        User.apartamento,
        Acesso.status
    ).join(Profissional, Acesso.profissional_id == Profissional.id)\
     .join(User, Acesso.usuario_morador_id == User.id)\
     .filter(Acesso.condominio_id == condominio_id)\
     .filter(func.date(Acesso.data_acesso) == hoje)\
     .order_by(Acesso.data_acesso.desc())\
     .limit(limite)\
     .all()

def get_relatorio_acessos(condominio_id, data_inicio, data_fim):
    """
    Busca todos os acessos de um condomínio em um intervalo de datas.
    """
    data_fim_ajustada = data_fim + timedelta(days=1)
    
    return db.session.query(
        Acesso.data_acesso,
        Acesso.data_saida,
        Profissional.nome,
        User.nome.label('morador_nome'),
        User.apartamento,
        Acesso.status,
        Acesso.servico
    ).join(Profissional, Acesso.profissional_id == Profissional.id)\
     .join(User, Acesso.usuario_morador_id == User.id)\
     .filter(Acesso.condominio_id == condominio_id)\
     .filter(Acesso.data_acesso >= data_inicio)\
     .filter(Acesso.data_acesso < data_fim_ajustada)\
     .order_by(Acesso.data_acesso)\
     .all()

# --- Funções para Administradores ---

def get_all_users():
    """
    Retorna todos os usuários do sistema.
    """
    return User.query.all()

def get_all_condominios():
    """
    Busca todos os condomínios do sistema, ordenados por nome.
    """
    return Condominio.query.order_by(Condominio.nome).all()

def create_user_admin(form_data):
    """
    Cria um novo usuário com base nos dados do formulário do administrador.
    A senha é armazenada com hash por segurança.
    """
    try:
        hashed_password = generate_password_hash(form_data['password'])

        condominio_id_from_form = form_data.get('condominio_id')
        condominio_id = int(condominio_id_from_form) if condominio_id_from_form and condominio_id_from_form != '-1' else None
        
        user = User(
            nome=form_data['nome'],
            email=form_data['email'],
            senha_hash=hashed_password,
            role=form_data['role'],
            apartamento=form_data.get('apartamento'),
            condominio_id=condominio_id
        )
        
        db.session.add(user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar usuário: {e}")
        return False

def create_condominio_admin(form_data):
    """
    Cria um novo condomínio com base nos dados do formulário.
    """
    try:
        plano_id_from_form = form_data.get('plano_id')
        
        if plano_id_from_form and plano_id_from_form != '-1':
            plano_id = int(plano_id_from_form)
        else:
            plano_id = None
            
        condominio = Condominio(
            nome=form_data['nome'],
            endereco=form_data['endereco'],
            status_assinatura=form_data['status_assinatura'],
            plano_id=plano_id
        )
        db.session.add(condominio)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar condomínio: {e}")
        return False

def get_user_by_id(user_id):
    """
    Busca um usuário pelo ID.
    """
    return User.query.get(user_id)

def update_user_admin(user_id, form_data):
    """
    Atualiza um usuário existente com base nos dados do formulário do administrador.
    """
    user = get_user_by_id(user_id)
    if user:
        user.nome = form_data['nome']
        user.email = form_data['email']
        user.role = form_data['role']
        user.apartamento = form_data.get('apartamento') or None
        
        if form_data.get('password'):
            user.senha_hash = generate_password_hash(form_data['password'])

        condominio_id_from_form = form_data.get('condominio_id')
        user.condominio_id = int(condominio_id_from_form) if condominio_id_from_form and condominio_id_from_form != '-1' else None
        
        db.session.commit()
        return True
    return False

def delete_user_admin(user_id):
    """
    Exclui um usuário do sistema.
    """
    user = get_user_by_id(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False

def get_condominio_by_id(condominio_id):
    """
    Busca um condomínio pelo ID.
    """
    return Condominio.query.get(condominio_id)

def get_all_planos():
    """
    Retorna todos os planos de assinatura disponíveis.
    """
    return Plano.query.all()

def update_condominio_admin(condominio_id, form_data):
    """
    Atualiza um condomínio existente com base nos dados do formulário do administrador.
    """
    condominio = get_condominio_by_id(condominio_id)
    if condominio:
        condominio.nome = form_data['nome']
        condominio.endereco = form_data['endereco']
        condominio.status_assinatura = form_data['status_assinatura']
        plano_id_from_form = form_data.get('plano_id')
        condominio.plano_id = int(plano_id_from_form) if plano_id_from_form and plano_id_from_form != '-1' else None
        
        db.session.commit()
        return True
    return False

def delete_condominio_admin(condominio_id):
    """
    Exclui um condomínio do sistema.
    """
    condominio = get_condominio_by_id(condominio_id)
    if condominio:
        db.session.delete(condominio)
        db.session.commit()
        return True
    return False

def get_all_moradores_do_condominio(condominio_id):
    """
    Busca todos os usuários com o papel 'morador' em um condomínio específico.
    """
    return User.query.filter_by(condominio_id=condominio_id, role='morador').all()

# --- Funções de Relatório ---

def calcular_tempo_economizado(condominio_id, tempo_por_acesso_min=5):
    """
    Calcula o tempo total economizado para um condomínio no mês atual.
    
    Args:
        condominio_id: O ID do condomínio.
        tempo_por_acesso_min: O tempo médio economizado por acesso em minutos.
        
    Returns:
        O tempo total economizado em horas e minutos.
    """
    hoje = datetime.utcnow()
    primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    total_acessos_mes = Acesso.query.filter(
        Acesso.condominio_id == condominio_id,
        Acesso.data_acesso >= primeiro_dia_mes,
        Acesso.status.in_(['finalizado', 'autorizado'])
    ).count()
    
    total_minutos_economizados = total_acessos_mes * tempo_por_acesso_min
    
    horas = total_minutos_economizados // 60
    minutos = total_minutos_economizados % 60
    
    return f"{horas}h {minutos}m"

def calcular_tempo_economizado_total(condominio_id, tempo_por_acesso_min=5):
    """
    Calcula o tempo total economizado para um condomínio desde o início da operação.
    """
    total_acessos = Acesso.query.filter(
        Acesso.condominio_id == condominio_id,
        Acesso.status.in_(['finalizado', 'autorizado'])
    ).count()
    
    total_minutos_economizados = total_acessos * tempo_por_acesso_min
    
    horas = total_minutos_economizados // 60
    minutos = total_minutos_economizados % 60
    
    return f"{horas}h {minutos}m"

def contar_moradores_condominio(condominio_id):
    """
    Conta o número total de usuários do tipo 'morador' em um condomínio.
    """
    return User.query.filter_by(condominio_id=condominio_id, role='morador').count()

def contar_profissionais_condominio(condominio_id):
    """
    Conta o número total de profissionais que já acessaram um condomínio.
    """
    profissionais_ids = db.session.query(Acesso.profissional_id).filter_by(condominio_id=condominio_id).distinct().all()
    
    return len(profissionais_ids)

def get_acessos_em_andamento(condominio_id):
    """
    Busca todos os acessos de profissionais que entraram no condomínio
    mas ainda não registraram a saída.
    """
    return db.session.query(
        Acesso,
        Profissional.nome.label('nome_profissional'),
        User.apartamento.label('apartamento_morador'),
        User.nome.label('nome_morador')
    ).join(Profissional, Acesso.profissional_id == Profissional.id)\
    .join(User, Acesso.usuario_morador_id == User.id)\
    .filter(
        Acesso.condominio_id == condominio_id,
        Acesso.data_acesso.isnot(None),
        Acesso.data_saida.is_(None)
    ).order_by(Acesso.data_acesso.desc()).all()