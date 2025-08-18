# app/models.py
from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, index=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(64), default='morador')
    apartamento = db.Column(db.String(32))
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'))
    
    # NOVOS CAMPOS PARA VINCULAR AO PROFISSIONAL E RASTREAR INDICAÇÕES
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    referral_code = db.Column(db.String(32), unique=True, index=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # RELAÇÃO COM A PORTARIA (NOVO)
    portaria_id = db.Column(db.Integer, db.ForeignKey('portarias.id'))
    
    # Relações
    condominio = db.relationship('Condominio', back_populates='usuarios')
    profissional = db.relationship('Profissional', back_populates='usuario_acesso')
    
    # Relação de indicação (referral)
    referrals = db.relationship(
        'User', 
        backref=db.backref('referred_by', remote_side=[id])
    )

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    
    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.nome} ({self.role})>'

class Condominio(db.Model):
    __tablename__ = 'condominios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), unique=True, nullable=False)
    endereco = db.Column(db.String(255), nullable=False)
    status_assinatura = db.Column(db.String(64), default='inativo')
    data_fim_carencia = db.Column(db.DateTime)
    
    plano_id = db.Column(db.Integer, db.ForeignKey('planos.id'))
    
    # Relações
    plano = db.relationship('Plano', back_populates='condominios')
    usuarios = db.relationship('User', back_populates='condominio')
    acessos = db.relationship('Acesso', back_populates='condominio')
    
    # RELAÇÃO COM PORTARIAS (NOVO)
    portarias = db.relationship('Portaria', backref='condominio', lazy=True)

    def __repr__(self):
        return f'<Condominio {self.nome}>'

class Plano(db.Model):
    __tablename__ = 'planos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), unique=True, nullable=False)
    valor_mensal = db.Column(db.Numeric(10, 2), nullable=False)
    dias_carencia = db.Column(db.Integer, default=0)
    
    # Relações
    condominios = db.relationship('Condominio', back_populates='plano')

    def __repr__(self):
        return f'<Plano {self.nome}>'

class Profissional(db.Model):
    __tablename__ = 'profissionais'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    placa_veiculo = db.Column(db.String(10))
    empresa = db.Column(db.String(128)) 
    url_foto = db.Column(db.String(256)) 
    
    # Relações
    acessos = db.relationship('Acesso', back_populates='profissional')
    
    # NOVA RELAÇÃO COM O USUÁRIO DE ACESSO
    usuario_acesso = db.relationship('User', back_populates='profissional', uselist=False)

    def __repr__(self):
        return f'<Profissional {self.nome}>'

class Acesso(db.Model):
    __tablename__ = 'acessos'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(64), default='pendente')
    servico = db.Column(db.String(256))
    empresa = db.Column(db.String(256))
    tipo_acesso = db.Column(db.String(15))
    observacoes_morador = db.Column(db.Text)
    
    data_prevista_acesso = db.Column(db.Date)
    data_acesso = db.Column(db.DateTime)
    data_saida = db.Column(db.DateTime)
    
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'))
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    usuario_morador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario_porteiro_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # NOVO CAMPO PARA A PORTARIA
    portaria_id = db.Column(db.Integer, db.ForeignKey('portarias.id'))
    
    # Relações
    condominio = db.relationship('Condominio', back_populates='acessos')
    profissional = db.relationship('Profissional', back_populates='acessos')
    morador = db.relationship('User', foreign_keys=[usuario_morador_id])
    porteiro = db.relationship('User', foreign_keys=[usuario_porteiro_id])
    portaria = db.relationship('Portaria', back_populates='acessos')

    def __repr__(self):
        return f'<Acesso {self.id} | Status: {self.status}>'

class Portaria(db.Model):
    __tablename__ = 'portarias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'), nullable=False)
    # Relação com usuários (porteiros)
    usuarios = db.relationship('User', backref='portaria', lazy=True)
    # RELAÇÃO COM ACESSOS (NOVO)
    acessos = db.relationship('Acesso', back_populates='portaria', lazy=True)