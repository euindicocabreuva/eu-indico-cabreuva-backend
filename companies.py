from flask import Blueprint, request, jsonify, send_from_directory
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image

from src.models.cms import db, Company, CompanyPhoto, Review
from src.routes.auth import require_admin

companies_bp = Blueprint('companies', __name__)

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@companies_bp.route('/companies', methods=['GET'])
@cross_origin()
def get_companies():
    """Listar todas as empresas (com filtros)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category')
        approved_only = request.args.get('approved_only', 'true').lower() == 'true'
        search = request.args.get('search')
        
        query = Company.query
        
        if approved_only:
            query = query.filter(Company.approved == True)
        
        if category:
            query = query.filter(Company.category == category)
        
        if search:
            query = query.filter(
                db.or_(
                    Company.name.contains(search),
                    Company.description.contains(search)
                )
            )
        
        query = query.order_by(Company.featured.desc(), Company.created_at.desc())
        
        companies = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'companies': [company.to_dict() for company in companies.items],
            'total': companies.total,
            'pages': companies.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@companies_bp.route('/companies/<int:company_id>', methods=['GET'])
@cross_origin()
def get_company(company_id):
    """Obter detalhes de uma empresa específica"""
    try:
        company = Company.query.get_or_404(company_id)
        return jsonify({'company': company.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@companies_bp.route('/companies', methods=['POST'])
@cross_origin()
def create_company():
    """Criar nova empresa"""
    try:
        data = request.json
        
        company = Company(
            name=data.get('name'),
            description=data.get('description'),
            category=data.get('category'),
            address=data.get('address'),
            phone=data.get('phone'),
            email=data.get('email'),
            website=data.get('website'),
            plan=data.get('plan', 'basico'),
            approved=False  # Sempre começa não aprovada
        )
        
        db.session.add(company)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'company': company.to_dict(),
            'message': 'Empresa criada com sucesso. Aguardando aprovação.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@companies_bp.route('/companies/<int:company_id>', methods=['PUT'])
@cross_origin()
@require_admin
def update_company(company_id):
    """Atualizar empresa (apenas admin)"""
    try:
        company = Company.query.get_or_404(company_id)
        data = request.json
        
        # Atualizar campos
        for field in ['name', 'description', 'category', 'address', 'phone', 'email', 'website', 'plan', 'approved', 'featured']:
            if field in data:
                setattr(company, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'company': company.to_dict(),
            'message': 'Empresa atualizada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@companies_bp.route('/companies/<int:company_id>', methods=['DELETE'])
@cross_origin()
@require_admin
def delete_company(company_id):
    """Deletar empresa (apenas admin)"""
    try:
        company = Company.query.get_or_404(company_id)
        
        # Deletar fotos associadas
        for photo in company.photos:
            photo_path = os.path.join(UPLOAD_FOLDER, photo.filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        db.session.delete(company)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Empresa deletada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@companies_bp.route('/companies/<int:company_id>/photos', methods=['POST'])
@cross_origin()
def upload_company_photo(company_id):
    """Upload de foto para empresa"""
    try:
        company = Company.query.get_or_404(company_id)
        
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if file and allowed_file(file.filename):
            create_upload_folder()
            
            # Gerar nome único para o arquivo
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Salvar e redimensionar a imagem
            image = Image.open(file.stream)
            
            # Redimensionar mantendo proporção (máximo 1200x800)
            image.thumbnail((1200, 800), Image.Resampling.LANCZOS)
            
            # Salvar como JPEG para otimizar tamanho
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            
            image.save(filepath, "JPEG", quality=85, optimize=True)
            
            # Criar registro no banco
            photo = CompanyPhoto(
                company_id=company_id,
                filename=filename,
                original_name=file.filename,
                is_main=len(company.photos) == 0  # Primeira foto é a principal
            )
            
            db.session.add(photo)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'photo': photo.to_dict(),
                'message': 'Foto enviada com sucesso'
            }), 201
        
        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@companies_bp.route('/photos/<filename>')
@cross_origin()
def serve_photo(filename):
    """Servir fotos uploadadas"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({'error': 'Foto não encontrada'}), 404

