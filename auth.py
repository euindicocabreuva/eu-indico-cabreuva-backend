from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_cors import cross_origin
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import os
import json

from src.models.cms import db, User

auth_bp = Blueprint('auth', __name__)

# Configurações do Google OAuth (você precisará configurar isso)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'your-google-client-id')

@auth_bp.route('/login/google', methods=['POST'])
@cross_origin()
def google_login():
    """Login via Google OAuth"""
    try:
        token = request.json.get('token')
        
        if not token:
            return jsonify({'error': 'Token não fornecido'}), 400
        
        # Verificar o token do Google
        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Token inválido')
                
            email = idinfo['email']
            name = idinfo['name']
            
        except ValueError:
            return jsonify({'error': 'Token inválido'}), 401
        
        # Verificar se o usuário existe ou criar um novo
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Criar novo usuário
            user = User(
                email=email,
                name=name,
                is_admin=False  # Por padrão, novos usuários não são admin
            )
            db.session.add(user)
            db.session.commit()
        
        # Criar sessão
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['is_admin'] = user.is_admin
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'redirect_url': '/admin' if user.is_admin else '/dashboard'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login/admin', methods=['POST'])
@cross_origin()
def admin_login():
    """Login direto para admin (desenvolvimento)"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Para desenvolvimento, vamos aceitar um email/senha específico
        if email == 'admin@euindicocabreuva.com.br' and password == 'admin123':
            # Verificar se o usuário admin existe
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Criar usuário admin
                user = User(
                    email=email,
                    name='Administrador',
                    is_admin=True
                )
                db.session.add(user)
                db.session.commit()
            
            # Criar sessão
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['is_admin'] = user.is_admin
            
            return jsonify({
                'success': True,
                'user': user.to_dict(),
                'redirect_url': '/admin'
            })
        else:
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@cross_origin()
def logout():
    """Logout do usuário"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

@auth_bp.route('/me', methods=['GET'])
@cross_origin()
def get_current_user():
    """Obter informações do usuário atual"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify({'user': user.to_dict()})

@auth_bp.route('/check-admin', methods=['GET'])
@cross_origin()
def check_admin():
    """Verificar se o usuário é admin"""
    if 'user_id' not in session:
        return jsonify({'is_admin': False, 'authenticated': False})
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'is_admin': False, 'authenticated': False})
    
    return jsonify({
        'is_admin': user.is_admin,
        'authenticated': True,
        'user': user.to_dict()
    })

def require_admin(f):
    """Decorator para rotas que requerem admin"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

