import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.main import app
from src.models.admin import Admin, db
from src.models.business import Business
from src.models.flipbook import Flipbook

with app.app_context():
    # Criar admin padrão se não existir
    admin = Admin.query.first()
    if not admin:
        admin = Admin(
            username='admin',
            email='admin@euindicocabreuva.com.br',
            full_name='Administrador'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print('Admin criado: admin/admin123')
    
    # Criar algumas empresas de exemplo
    if Business.query.count() == 0:
        businesses = [
            Business(
                name='Restaurante Exemplo',
                description='Culinária brasileira com ingredientes locais',
                category='Alimentação',
                address='Centro, Cabreúva',
                phone='(11) 4528-1001',
                email='contato@restauranteexemplo.com.br',
                plan='master_plus',
                rating=4.8,
                review_count=47,
                featured=True
            ),
            Business(
                name='Clínica Saúde+',
                description='Atendimento médico especializado',
                category='Saúde',
                address='Jacaré, Cabreúva',
                phone='(11) 4528-1002',
                email='contato@clinicasaude.com.br',
                plan='avancado',
                rating=4.2,
                review_count=23,
                featured=True
            ),
            Business(
                name='Supermercado Local',
                description='Produtos frescos e de qualidade',
                category='Comércio',
                address='Centro, Cabreúva',
                phone='(11) 4528-1003',
                email='contato@supermercadolocal.com.br',
                plan='intermediario',
                rating=4.6,
                review_count=89,
                featured=True
            )
        ]
        
        for business in businesses:
            db.session.add(business)
        print('Empresas de exemplo criadas')
    
    # Criar flipbook de exemplo
    if Flipbook.query.count() == 0:
        flipbook = Flipbook(
            title='Revista Digital Cabreúva - Edição 1',
            description='Primeira edição da revista digital de Cabreúva',
            category='Geral',
            flipbook_url='https://issuu.com/exemplo',
            thumbnail_url='https://via.placeholder.com/300x400',
            featured=True
        )
        db.session.add(flipbook)
        print('Flipbook de exemplo criado')
    
    db.session.commit()
    print('Dados iniciais criados com sucesso!')

