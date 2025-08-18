# create_admin.py
from app.antigo_init import create_app
from app.models import User, db

def create_admin_user():
    """
    Cria um usuário administrador inicial se ele não existir.
    """
    app = create_app()
    with app.app_context():
        # Verifica se já existe um usuário com o email do admin
        existing_user = User.query.filter_by(email='admin@easygate.com').first()

        if existing_user:
            print("O usuário 'admin' já existe no banco de dados.")
            return

        print("Criando o usuário 'admin'...")
        
        # Cria a instância do usuário, usando 'role' em vez de 'user_type'
        admin_user = User(
            nome='Administrador', 
            email='admin@easygate.com', 
            role='admin'
        )
        
        # Define a senha usando o método correto 'set_senha'
        admin_user.set_senha('123')
        
        # Adiciona o usuário ao banco de dados e salva
        db.session.add(admin_user)
        db.session.commit()
        
        print("Usuário 'admin' criado com sucesso!")

if __name__ == '__main__':
    create_admin_user()