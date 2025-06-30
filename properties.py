from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import os
import uuid
from PIL import Image

from src.models.cms import db, Property, PropertyPhoto
from src.routes.auth import require_admin

properties_bp = Blueprint('properties', __name__)

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@properties_bp.route('/properties', methods=['GET'])
@cross_origin()
def get_properties():
    """Listar imóveis (com filtros)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        property_type = request.args.get('property_type')
        purpose = request.args.get('purpose')
        neighborhood = request.args.get('neighborhood')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        search = request.args.get('search')
        
        query = Property.query
        
        if active_only:
            query = query.filter(Property.active == True)
        
        if property_type:
            query = query.filter(Property.property_type == property_type)
        
        if purpose:
            query = query.filter(Property.purpose == purpose)
        
        if neighborhood:
            query = query.filter(Property.neighborhood.contains(neighborhood))
        
        if min_price:
            query = query.filter(Property.price >= min_price)
        
        if max_price:
            query = query.filter(Property.price <= max_price)
        
        if search:
            query = query.filter(
                db.or_(
                    Property.title.contains(search),
                    Property.description.contains(search),
                    Property.address.contains(search)
                )
            )
        
        query = query.order_by(Property.featured.desc(), Property.created_at.desc())
        
        properties = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'properties': [prop.to_dict() for prop in properties.items],
            'total': properties.total,
            'pages': properties.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/properties/<int:property_id>', methods=['GET'])
@cross_origin()
def get_property(property_id):
    """Obter detalhes de um imóvel específico"""
    try:
        property_obj = Property.query.get_or_404(property_id)
        return jsonify({'property': property_obj.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/properties', methods=['POST'])
@cross_origin()
def create_property():
    """Criar novo imóvel"""
    try:
        data = request.json
        
        property_obj = Property(
            title=data.get('title'),
            description=data.get('description'),
            property_type=data.get('property_type'),
            purpose=data.get('purpose'),
            price=data.get('price'),
            address=data.get('address'),
            neighborhood=data.get('neighborhood'),
            bedrooms=data.get('bedrooms'),
            bathrooms=data.get('bathrooms'),
            area=data.get('area'),
            contact_name=data.get('contact_name'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            active=True
        )
        
        db.session.add(property_obj)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'property': property_obj.to_dict(),
            'message': 'Imóvel criado com sucesso'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/properties/<int:property_id>', methods=['PUT'])
@cross_origin()
@require_admin
def update_property(property_id):
    """Atualizar imóvel (apenas admin)"""
    try:
        property_obj = Property.query.get_or_404(property_id)
        data = request.json
        
        # Atualizar campos
        for field in ['title', 'description', 'property_type', 'purpose', 'price', 'address', 'neighborhood', 'bedrooms', 'bathrooms', 'area', 'contact_name', 'contact_email', 'contact_phone', 'active', 'featured']:
            if field in data:
                setattr(property_obj, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'property': property_obj.to_dict(),
            'message': 'Imóvel atualizado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/properties/<int:property_id>', methods=['DELETE'])
@cross_origin()
@require_admin
def delete_property(property_id):
    """Deletar imóvel (apenas admin)"""
    try:
        property_obj = Property.query.get_or_404(property_id)
        
        # Deletar fotos associadas
        for photo in property_obj.photos:
            photo_path = os.path.join(UPLOAD_FOLDER, photo.filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        db.session.delete(property_obj)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Imóvel deletado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/properties/<int:property_id>/photos', methods=['POST'])
@cross_origin()
def upload_property_photo(property_id):
    """Upload de foto para imóvel"""
    try:
        property_obj = Property.query.get_or_404(property_id)
        
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
            photo = PropertyPhoto(
                property_id=property_id,
                filename=filename,
                original_name=file.filename,
                is_main=len(property_obj.photos) == 0  # Primeira foto é a principal
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

@properties_bp.route('/properties/<int:property_id>/photos/<int:photo_id>', methods=['DELETE'])
@cross_origin()
def delete_property_photo(property_id, photo_id):
    """Deletar foto do imóvel"""
    try:
        photo = PropertyPhoto.query.filter_by(
            id=photo_id, 
            property_id=property_id
        ).first_or_404()
        
        # Deletar arquivo físico
        photo_path = os.path.join(UPLOAD_FOLDER, photo.filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)
        
        db.session.delete(photo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Foto deletada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/properties/types', methods=['GET'])
@cross_origin()
def get_property_types():
    """Obter tipos de imóveis"""
    property_types = [
        'casa',
        'apartamento',
        'terreno',
        'comercial',
        'chacara',
        'sitio'
    ]
    
    return jsonify({'property_types': property_types})

@properties_bp.route('/properties/neighborhoods', methods=['GET'])
@cross_origin()
def get_neighborhoods():
    """Obter bairros de Cabreúva"""
    neighborhoods = [
        'Centro',
        'Jacaré',
        'Vilarejo',
        'Pinhal',
        'Bananal',
        'São Francisco',
        'Jundiuvira',
        'Bonfim',
        'Caí',
        'Piraí',
        'Guaxatuba',
        'Campininha',
        'Itaguá',
        'Barrinha'
    ]
    
    return jsonify({'neighborhoods': neighborhoods})

