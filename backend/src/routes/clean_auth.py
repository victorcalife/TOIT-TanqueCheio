from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from src.database import db
from src.models.clean_models import CleanUser
from datetime import timedelta
import traceback

clean_auth_bp = Blueprint('clean_auth', __name__)

@clean_auth_bp.route('/register', methods=['POST'])
def register():
    """Registro de usuário simplificado"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400
        
        # Verificar se email já existe
        existing_user = CleanUser.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Email já cadastrado'
            }), 409
        
        # Criar usuário
        user = CleanUser(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            preferred_fuel=data.get('preferred_fuel', 'gasoline')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Gerar tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'user': user.to_dict(),
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro no registro: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@clean_auth_bp.route('/login', methods=['POST'])
def login():
    """Login de usuário"""
    try:
        data = request.get_json()
        
        # Validar dados
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Email e senha são obrigatórios'
            }), 400
        
        # Buscar usuário
        user = CleanUser.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({
                'success': False,
                'error': 'Email ou senha inválidos'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Conta desativada'
            }), 401
        
        # Gerar tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 200
        
    except Exception as e:
        print(f"Erro no login: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'details': str(e)
        }), 500

@clean_auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtém dados do usuário atual"""
    try:
        user_id = get_jwt_identity()
        user = CleanUser.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Erro ao obter usuário: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@clean_auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Renova token de acesso"""
    try:
        user_id = get_jwt_identity()
        
        new_token = create_access_token(
            identity=user_id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'access_token': new_token
        }), 200
        
    except Exception as e:
        print(f"Erro no refresh: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

