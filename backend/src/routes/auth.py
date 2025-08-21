from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from src.database import db, blacklist_token, is_token_blacklisted, check_rate_limit
from src.models.user import User, UserSession
from src.models.user_profile import UserProfile
from datetime import datetime, timezone, timedelta
import hashlib
import uuid

auth_bp = Blueprint('auth', __name__)

def get_client_ip():
    """Get client IP address"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def hash_token(token):
    """Hash token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        # Rate limiting
        client_ip = get_client_ip()
        if check_rate_limit(f"register:{client_ip}", 5, 3600):  # 5 registrations per hour
            return jsonify({
                'success': False,
                'error': 'Muitas tentativas de registro. Tente novamente em 1 hora.'
            }), 429
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        phone = data.get('phone')
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({
                'success': False,
                'error': 'Formato de email inválido'
            }), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({
                'success': False,
                'error': 'Senha deve ter pelo menos 8 caracteres'
            }), 400
        
        # Check if user already exists
        if User.find_by_email(email):
            return jsonify({
                'success': False,
                'error': 'Email já cadastrado'
            }), 409
        
        # Create user
        user = User.create_user(
            email=email,
            password=password,
            name=name,
            phone=phone
        )
        
        # Create user profile
        profile = UserProfile.create_profile(user_id=user.id)
        
        # Generate tokens
        tokens = user.generate_tokens()
        
        # Create session
        access_token_hash = hash_token(tokens['access_token'])
        refresh_token_hash = hash_token(tokens['refresh_token'])
        expires_at = datetime.now(timezone.utc) + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        
        session = UserSession(
            user_id=user.id,
            token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            device_info=request.headers.get('User-Agent'),
            ip_address=client_ip
        )
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário registrado com sucesso',
            'data': {
                'user': user.to_dict(),
                'profile': profile.to_dict(),
                'tokens': tokens
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        # Rate limiting
        client_ip = get_client_ip()
        if check_rate_limit(f"login:{client_ip}", 10, 900):  # 10 attempts per 15 minutes
            return jsonify({
                'success': False,
                'error': 'Muitas tentativas de login. Tente novamente em 15 minutos.'
            }), 429
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Email e senha são obrigatórios'
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.find_by_email(email)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Credenciais inválidas'
            }), 401
        
        # Check password
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'error': 'Credenciais inválidas'
            }), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Conta desativada'
            }), 401
        
        # Update last login
        user.update_last_login()
        
        # Generate tokens
        tokens = user.generate_tokens()
        
        # Create session
        access_token_hash = hash_token(tokens['access_token'])
        refresh_token_hash = hash_token(tokens['refresh_token'])
        expires_at = datetime.now(timezone.utc) + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        
        session = UserSession(
            user_id=user.id,
            token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            device_info=request.headers.get('User-Agent'),
            ip_address=client_ip
        )
        db.session.add(session)
        db.session.commit()
        
        # Get user profile
        profile = UserProfile.find_by_user_id(user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'data': {
                'user': user.to_dict(),
                'profile': profile.to_dict() if profile else None,
                'tokens': tokens
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user
        user = User.query.get(current_user_id)
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado ou inativo'
            }), 401
        
        # Generate new access token
        additional_claims = {
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'is_active': user.is_active
        }
        
        new_access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': new_access_token,
                'token_type': 'Bearer'
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao renovar token'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user and blacklist token"""
    try:
        jti = get_jwt()['jti']
        current_user_id = get_jwt_identity()
        
        # Blacklist current token
        expires_in = current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
        blacklist_token(jti, int(expires_in))
        
        # Deactivate current session
        access_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if access_token:
            token_hash = hash_token(access_token)
            session = UserSession.query.filter_by(
                user_id=current_user_id,
                token_hash=token_hash,
                is_active=True
            ).first()
            
            if session:
                session.revoke()
        
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao fazer logout'
        }), 500

@auth_bp.route('/logout-all', methods=['POST'])
@jwt_required()
def logout_all():
    """Logout from all devices"""
    try:
        current_user_id = get_jwt_identity()
        
        # Revoke all user sessions
        UserSession.revoke_user_sessions(current_user_id)
        
        return jsonify({
            'success': True,
            'message': 'Logout realizado em todos os dispositivos'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout all error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao fazer logout'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado'
            }), 404
        
        # Get user profile
        profile = UserProfile.find_by_user_id(user.id)
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'profile': profile.to_dict() if profile else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get current user error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter dados do usuário'
        }), 500

@auth_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_sessions():
    """Get user active sessions"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get active sessions
        sessions = UserSession.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).order_by(UserSession.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': [session.to_dict() for session in sessions],
                'total': len(sessions)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get sessions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter sessões'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'Senha atual e nova senha são obrigatórias'
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Get user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado'
            }), 404
        
        # Check current password
        if not user.check_password(current_password):
            return jsonify({
                'success': False,
                'error': 'Senha atual incorreta'
            }), 401
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'error': 'Nova senha deve ter pelo menos 8 caracteres'
            }), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Revoke all other sessions (force re-login on other devices)
        UserSession.revoke_user_sessions(current_user_id)
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Change password error: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao alterar senha'
        }), 500

# JWT token blacklist checker
@auth_bp.before_app_request
def check_if_token_revoked():
    """Check if JWT token is blacklisted"""
    try:
        verify_jwt_in_request(optional=True)
        jti = get_jwt().get('jti') if get_jwt() else None
        
        if jti and is_token_blacklisted(jti):
            return jsonify({
                'success': False,
                'error': 'Token inválido'
            }), 401
            
    except Exception:
        # If there's any error in JWT verification, let it pass
        # The actual JWT verification will be handled by @jwt_required decorators
        pass

