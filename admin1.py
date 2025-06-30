from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from sqlalchemy import func

from src.models.cms import db, Company, News, Job, Property, Review, User, SiteSettings
from src.routes.auth import require_admin

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard/stats', methods=['GET'])
@cross_origin()
@require_admin
def get_dashboard_stats():
    """Obter estatísticas para o dashboard administrativo"""
    try:
        stats = {
            'companies': {
                'total': Company.query.count(),
                'approved': Company.query.filter_by(approved=True).count(),
                'pending': Company.query.filter_by(approved=False).count(),
                'featured': Company.query.filter_by(featured=True).count()
            },
            'news': {
                'total': News.query.count(),
                'published': News.query.filter_by(published=True).count(),
                'draft': News.query.filter_by(published=False).count(),
                'featured': News.query.filter_by(featured=True).count()
            },
            'jobs': {
                'total': Job.query.count(),
                'active': Job.query.filter_by(active=True).count(),
                'inactive': Job.query.filter_by(active=False).count()
            },
            'properties': {
                'total': Property.query.count(),
                'active': Property.query.filter_by(active=True).count(),
                'for_sale': Property.query.filter_by(purpose='venda', active=True).count(),
                'for_rent': Property.query.filter_by(purpose='locacao', active=True).count()
            },
            'reviews': {
                'total': Review.query.count(),
                'approved': Review.query.filter_by(approved=True).count(),
                'pending': Review.query.filter_by(approved=False).count()
            },
            'users': {
                'total': User.query.count(),
                'admins': User.query.filter_by(is_admin=True).count()
            }
        }
        
        # Estatísticas por categoria de empresa
        category_stats = db.session.query(
            Company.category,
            func.count(Company.id).label('count')
        ).filter_by(approved=True).group_by(Company.category).all()
        
        stats['categories'] = {cat: count for cat, count in category_stats}
        
        return jsonify({'stats': stats})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/companies/pending', methods=['GET'])
@cross_origin()
@require_admin
def get_pending_companies():
    """Obter empresas pendentes de aprovação"""
    try:
        companies = Company.query.filter_by(approved=False).order_by(Company.created_at.desc()).all()
        return jsonify({
            'companies': [company.to_dict() for company in companies]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/companies/<int:company_id>/approve', methods=['PUT'])
@cross_origin()
@require_admin
def approve_company(company_id):
    """Aprovar empresa"""
    try:
        company = Company.query.get_or_404(company_id)
        company.approved = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Empresa "{company.name}" aprovada com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/companies/<int:company_id>/reject', methods=['PUT'])
@cross_origin()
@require_admin
def reject_company(company_id):
    """Rejeitar empresa"""
    try:
        company = Company.query.get_or_404(company_id)
        company.approved = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Empresa "{company.name}" rejeitada'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/companies/<int:company_id>/feature', methods=['PUT'])
@cross_origin()
@require_admin
def toggle_company_feature(company_id):
    """Alternar destaque da empresa"""
    try:
        company = Company.query.get_or_404(company_id)
        company.featured = not company.featured
        db.session.commit()
        
        status = "destacada" if company.featured else "removida dos destaques"
        return jsonify({
            'success': True,
            'featured': company.featured,
            'message': f'Empresa "{company.name}" {status}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/reviews/pending', methods=['GET'])
@cross_origin()
@require_admin
def get_pending_reviews():
    """Obter avaliações pendentes de aprovação"""
    try:
        reviews = db.session.query(Review, Company.name).join(
            Company, Review.company_id == Company.id
        ).filter(Review.approved == False).order_by(Review.created_at.desc()).all()
        
        result = []
        for review, company_name in reviews:
            review_dict = review.to_dict()
            review_dict['company_name'] = company_name
            result.append(review_dict)
        
        return jsonify({'reviews': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/reviews/<int:review_id>/reject', methods=['DELETE'])
@cross_origin()
@require_admin
def reject_review(review_id):
    """Rejeitar/deletar avaliação"""
    try:
        review = Review.query.get_or_404(review_id)
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avaliação rejeitada e removida'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/settings', methods=['GET'])
@cross_origin()
@require_admin
def get_site_settings():
    """Obter configurações do site"""
    try:
        settings = SiteSettings.query.all()
        settings_dict = {setting.key: setting.value for setting in settings}
        
        # Configurações padrão se não existirem
        default_settings = {
            'site_title': 'Eu Indico Cabreúva',
            'site_description': 'Guia Completo da Cidade',
            'contact_phone': '(11) 4528-1000',
            'contact_email': 'contato@euindicocabreuva.com.br',
            'hero_background_color': '#065f46',
            'primary_color': '#10b981',
            'secondary_color': '#059669'
        }
        
        for key, default_value in default_settings.items():
            if key not in settings_dict:
                settings_dict[key] = default_value
        
        return jsonify({'settings': settings_dict})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/settings', methods=['PUT'])
@cross_origin()
@require_admin
def update_site_settings():
    """Atualizar configurações do site"""
    try:
        data = request.json
        
        for key, value in data.items():
            setting = SiteSettings.query.filter_by(key=key).first()
            
            if setting:
                setting.value = value
            else:
                setting = SiteSettings(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configurações atualizadas com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@cross_origin()
@require_admin
def get_users():
    """Listar todos os usuários"""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['PUT'])
@cross_origin()
@require_admin
def toggle_user_admin(user_id):
    """Alternar status de admin do usuário"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_admin = not user.is_admin
        db.session.commit()
        
        status = "promovido a administrador" if user.is_admin else "removido da administração"
        return jsonify({
            'success': True,
            'is_admin': user.is_admin,
            'message': f'Usuário "{user.name}" {status}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

