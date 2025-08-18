# populate_db.py
from app import create_app, db
from app.models import User, Condominio, Plano, Profissional, Acesso, Portaria
from datetime import datetime, timedelta
import random

def populate_db():
    app = create_app()
    with app.app_context():
        print("Iniciando a população do banco de dados com novos dados...")
        
        # Limpar tabelas existentes para evitar duplicação em testes
        db.session.query(Acesso).delete()
        db.session.query(Profissional).delete()
        db.session.query(User).delete()
        db.session.query(Portaria).delete()
        db.session.query(Condominio).delete()
        db.session.query(Plano).delete()
        db.session.commit()
        print("Tabelas limpas.")

        # 1. Cria um plano de exemplo
        plano = Plano(nome='Plano Pro', valor_mensal=500.00, dias_carencia=30)
        db.session.add(plano)
        db.session.commit()
        print("Plano 'Plano Pro' criado.")

        # 2. Cria condomínios e suas portarias
        condominios_criados = []
        for i in range(1, 5):
            condominio = Condominio(
                nome=f'Condominio Exemplo {i}',
                endereco=f'Rua Teste, {i}',
                status_assinatura='ativo',
                plano_id=plano.id,
                data_fim_carencia=datetime.now() + timedelta(days=30)
            )
            db.session.add(condominio)
            condominios_criados.append(condominio)
        db.session.commit()
        
        portarias_criadas = []
        for condominio in condominios_criados:
            num_portarias = 1 if condominio.nome == 'Condominio Exemplo 1' else random.randint(2, 4)
            for i in range(1, num_portarias + 1):
                portaria = Portaria(nome=f'Portaria {i}', condominio=condominio)
                db.session.add(portaria)
                portarias_criadas.append(portaria)
        db.session.commit()
        print(f"{len(condominios_criados)} condomínios e {len(portarias_criadas)} portarias criadas.")
        
        # 3. Cria usuários de teste
        
        # Admin
        admin = User(nome='Admin', email='admin@easygate.com', role='admin')
        admin.set_senha('123')
        db.session.add(admin)

        # Síndicos
        sindico1 = User(nome='Sindico Um', email='sindico1@easygate.com', role='sindico', condominio_id=condominios_criados[0].id)
        sindico1.set_senha('123')
        db.session.add(sindico1)
        sindico2 = User(nome='Sindico Dois', email='sindico2@easygate.com', role='sindico', condominio_id=condominios_criados[1].id)
        sindico2.set_senha('123')
        db.session.add(sindico2)
        
        # Porteiros (agora associados a portarias)
        porteiro1 = User(nome='Porteiro Um', email='porteiro1@easygate.com', role='porteiro', portaria_id=portarias_criadas[0].id)
        porteiro1.set_senha('123')
        db.session.add(porteiro1)

        porteiro2 = User(nome='Porteiro Dois', email='porteiro2@easygate.com', role='porteiro', portaria_id=portarias_criadas[1].id)
        porteiro2.set_senha('123')
        db.session.add(porteiro2)
        
        # Morador
        morador1 = User(nome='Morador Um', email='morador1@easygate.com', role='morador', apartamento='101-A', condominio_id=condominios_criados[0].id)
        morador1.set_senha('123')
        db.session.add(morador1)
        morador2 = User(nome='Morador Dois', email='morador2@easygate.com', role='morador', apartamento='202-B', condominio_id=condominios_criados[1].id)
        morador2.set_senha('123')
        db.session.add(morador2)

        # Profissionais
        profissional1 = Profissional(nome='Entregador Uber', placa_veiculo='ABC-1234', empresa='Uber Eats')
        profissional2 = Profissional(nome='Tecnico de Internet', empresa='Fibra Net')
        profissional3 = Profissional(nome='Encanador Rapido', empresa='Encanamentos Brasil')
        db.session.add_all([profissional1, profissional2, profissional3])
        
        db.session.flush() # Forçar a criação dos IDs antes do commit

        # 4. Cria acessos de teste, agora associados a portarias
        
        # Acesso pendente - Condominio 1, Portaria 1
        acesso_pendente1 = Acesso(
            status='pendente',
            tipo_acesso='qrcode',
            data_acesso=datetime.now(),
            condominio_id=condominios_criados[0].id,
            profissional_id=profissional1.id,
            portaria_id=portarias_criadas[0].id
        )
        db.session.add(acesso_pendente1)
        print("Acesso 'pendente' criado para Condominio 1, Portaria 1.")

        # Acesso pendente - Condominio 2, Portaria 2
        acesso_pendente2 = Acesso(
            status='pendente',
            tipo_acesso='qrcode',
            data_acesso=datetime.now(),
            condominio_id=condominios_criados[1].id,
            profissional_id=profissional2.id,
            portaria_id=portarias_criadas[2].id
        )
        db.session.add(acesso_pendente2)
        print("Acesso 'pendente' criado para Condominio 2, Portaria 2.")
        
        # Acesso finalizado - Condominio 1, Portaria 1
        acesso_finalizado = Acesso(
            status='finalizado',
            tipo_acesso='qrcode',
            data_acesso=datetime.now() - timedelta(hours=2),
            data_saida=datetime.now() - timedelta(hours=1),
            condominio_id=condominios_criados[0].id,
            profissional_id=profissional3.id,
            portaria_id=portarias_criadas[0].id,
            usuario_porteiro_id=porteiro1.id
        )
        db.session.add(acesso_finalizado)
        print("Acesso 'finalizado' criado para Condominio 1, Portaria 1.")


        db.session.commit()
        print("\nPopulação do banco de dados concluída.")

if __name__ == '__main__':
    populate_db()