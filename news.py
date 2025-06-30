from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from src.models.cms import db, News
from src.routes.auth import require_admin

news_bp = Blueprint('news', __name__)

@news_bp.route('/news', methods=['GET'])
@cross_origin()
def get_news():
    """Listar notícias (com filtros)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category')
        published_only = request.args.get('published_only', 'true').lower() == 'true'
        search = request.args.get('search')
        
        query = News.query
        
        if published_only:
            query = query.filter(News.published == True)
        
        if category:
            query = query.filter(News.category == category)
        
        if search:
            query = query.filter(
                db.or_(
                    News.title.contains(search),
                    News.content.contains(search)
                )
            )
        
        query = query.order_by(News.featured.desc(), News.created_at.desc())
        
        news = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'news': [article.to_dict() for article in news.items],
            'total': news.total,
            'pages': news.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/<int:news_id>', methods=['GET'])
@cross_origin()
def get_news_article(news_id):
    """Obter detalhes de uma notícia específica"""
    try:
        article = News.query.get_or_404(news_id)
        
        # Incrementar visualizações
        article.views += 1
        db.session.commit()
        
        return jsonify({'news': article.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news', methods=['POST'])
@cross_origin()
@require_admin
def create_news():
    """Criar nova notícia (apenas admin)"""
    try:
        data = request.json
        
        article = News(
            title=data.get('title'),
            content=data.get('content'),
            category=data.get('category'),
            author=data.get('author'),
            featured=data.get('featured', False),
            urgent=data.get('urgent', False),
            published=data.get('published', False),
            image_url=data.get('image_url')
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'news': article.to_dict(),
            'message': 'Notícia criada com sucesso'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/<int:news_id>', methods=['PUT'])
@cross_origin()
@require_admin
def update_news(news_id):
    """Atualizar notícia (apenas admin)"""
    try:
        article = News.query.get_or_404(news_id)
        data = request.json
        
        # Atualizar campos
        for field in ['title', 'content', 'category', 'author', 'featured', 'urgent', 'published', 'image_url']:
            if field in data:
                setattr(article, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'news': article.to_dict(),
            'message': 'Notícia atualizada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/<int:news_id>', methods=['DELETE'])
@cross_origin()
@require_admin
def delete_news(news_id):
    """Deletar notícia (apenas admin)"""
    try:
        article = News.query.get_or_404(news_id)
        db.session.delete(article)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notícia deletada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/categories', methods=['GET'])
@cross_origin()
def get_news_categories():
    """Obter categorias de notícias"""
    categories = [
        'prefeitura',
        'eventos',
        'obras',
        'saude',
        'educacao',
        'turismo',
        'economia',
        'cultura',
        'esportes',
        'meio-ambiente'
    ]
    
    return jsonify({'categories': categories})

@news_bp.route('/news/featured', methods=['GET'])
@cross_origin()
def get_featured_news():
    """Obter notícias em destaque"""
    try:
        featured_news = News.query.filter_by(
            featured=True, 
            published=True
        ).order_by(News.created_at.desc()).limit(5).all()
        
        return jsonify({
            'news': [article.to_dict() for article in featured_news]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/urgent', methods=['GET'])
@cross_origin()
def get_urgent_news():
    """Obter notícias urgentes"""
    try:
        urgent_news = News.query.filter_by(
            urgent=True, 
            published=True
        ).order_by(News.created_at.desc()).limit(3).all()
        
        return jsonify({
            'news': [article.to_dict() for article in urgent_news]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

