from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from src.models.cms import db, Job
from src.routes.auth import require_admin

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/jobs', methods=['GET'])
@cross_origin()
def get_jobs():
    """Listar vagas de emprego (com filtros)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category = request.args.get('category')
        location = request.args.get('location')
        contract_type = request.args.get('contract_type')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        search = request.args.get('search')
        
        query = Job.query
        
        if active_only:
            query = query.filter(Job.active == True)
        
        if category:
            query = query.filter(Job.category == category)
        
        if location:
            query = query.filter(Job.location.contains(location))
        
        if contract_type:
            query = query.filter(Job.contract_type == contract_type)
        
        if search:
            query = query.filter(
                db.or_(
                    Job.title.contains(search),
                    Job.description.contains(search),
                    Job.company_name.contains(search)
                )
            )
        
        query = query.order_by(Job.created_at.desc())
        
        jobs = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'jobs': [job.to_dict() for job in jobs.items],
            'total': jobs.total,
            'pages': jobs.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/jobs/<int:job_id>', methods=['GET'])
@cross_origin()
def get_job(job_id):
    """Obter detalhes de uma vaga específica"""
    try:
        job = Job.query.get_or_404(job_id)
        return jsonify({'job': job.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/jobs', methods=['POST'])
@cross_origin()
def create_job():
    """Criar nova vaga de emprego"""
    try:
        data = request.json
        
        job = Job(
            title=data.get('title'),
            company_name=data.get('company_name'),
            description=data.get('description'),
            location=data.get('location'),
            salary=data.get('salary'),
            contract_type=data.get('contract_type'),
            category=data.get('category'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            active=True
        )
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job': job.to_dict(),
            'message': 'Vaga criada com sucesso'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@cross_origin()
@require_admin
def update_job(job_id):
    """Atualizar vaga (apenas admin)"""
    try:
        job = Job.query.get_or_404(job_id)
        data = request.json
        
        # Atualizar campos
        for field in ['title', 'company_name', 'description', 'location', 'salary', 'contract_type', 'category', 'contact_email', 'contact_phone', 'active']:
            if field in data:
                setattr(job, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job': job.to_dict(),
            'message': 'Vaga atualizada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@cross_origin()
@require_admin
def delete_job(job_id):
    """Deletar vaga (apenas admin)"""
    try:
        job = Job.query.get_or_404(job_id)
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Vaga deletada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/jobs/categories', methods=['GET'])
@cross_origin()
def get_job_categories():
    """Obter categorias de emprego"""
    categories = [
        'administracao',
        'vendas',
        'producao',
        'servicos',
        'saude',
        'educacao',
        'tecnologia',
        'construcao',
        'alimentacao',
        'turismo'
    ]
    
    return jsonify({'categories': categories})

@jobs_bp.route('/jobs/contract-types', methods=['GET'])
@cross_origin()
def get_contract_types():
    """Obter tipos de contrato"""
    contract_types = [
        'CLT',
        'PJ',
        'Temporario',
        'Estagio',
        'Freelancer'
    ]
    
    return jsonify({'contract_types': contract_types})

