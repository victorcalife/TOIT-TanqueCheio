#!/usr/bin/env python3
"""
Script de debug para testar autenticação e conexão com banco
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database import db
from src.models.simple_models import User, UserProfile
from src.config import config
from flask import Flask
import traceback

def test_database_connection():
    """Testa conexão com banco de dados"""
    try:
        app = Flask(__name__)
        app.config.from_object(config['development'])
        
        with app.app_context():
            from src.database import init_database
            init_database(app)
            
            # Testar conexão
            result = db.session.execute(db.text('SELECT 1')).fetchone()
            print(f"✅ Conexão com banco OK: {result}")
            
            # Listar tabelas
            tables = db.session.execute(db.text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)).fetchall()
            
            print(f"📋 Tabelas no banco: {[t[0] for t in tables]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        traceback.print_exc()
        return False

def test_user_creation():
    """Testa criação de usuário"""
    try:
        app = Flask(__name__)
        app.config.from_object(config['development'])
        
        with app.app_context():
            from src.database import init_database
            init_database(app)
            
            # Criar tabelas se não existirem
            db.create_all()
            print("✅ Tabelas criadas/verificadas")
            
            # Tentar criar usuário
            user = User(
                name="Teste Debug",
                email="debug@test.com",
                phone="+55 11 99999-9999"
            )
            user.set_password("senha123")
            
            db.session.add(user)
            db.session.commit()
            
            print(f"✅ Usuário criado: {user.id}")
            
            # Criar perfil
            profile = UserProfile(
                user_id=user.id,
                preferred_fuel='gasoline'
            )
            
            db.session.add(profile)
            db.session.commit()
            
            print(f"✅ Perfil criado: {profile.id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na criação: {e}")
        traceback.print_exc()
        return False

def test_auth_endpoint():
    """Testa endpoint de autenticação"""
    try:
        app = Flask(__name__)
        app.config.from_object(config['production'])
        
        with app.app_context():
            from src.database import init_database
            from flask_jwt_extended import JWTManager
            
            init_database(app)
            jwt = JWTManager(app)
            
            # Importar rota de auth
            from src.routes.auth import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            
            # Testar com cliente de teste
            with app.test_client() as client:
                response = client.post('/api/auth/register', 
                    json={
                        'name': 'Teste API',
                        'email': 'api@test.com',
                        'phone': '+55 11 88888-8888',
                        'password': 'senha123',
                        'preferred_fuel': 'gasoline'
                    },
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"📡 Status: {response.status_code}")
                print(f"📡 Response: {response.get_json()}")
                
                return response.status_code == 201
                
    except Exception as e:
        print(f"❌ Erro no endpoint: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔍 Iniciando debug da autenticação...")
    print("=" * 50)
    
    print("\n1. Testando conexão com banco...")
    db_ok = test_database_connection()
    
    if db_ok:
        print("\n2. Testando criação de usuário...")
        user_ok = test_user_creation()
        
        if user_ok:
            print("\n3. Testando endpoint de auth...")
            auth_ok = test_auth_endpoint()
            
            if auth_ok:
                print("\n✅ Todos os testes passaram!")
            else:
                print("\n❌ Falha no teste de endpoint")
        else:
            print("\n❌ Falha na criação de usuário")
    else:
        print("\n❌ Falha na conexão com banco")
    
    print("=" * 50)
    print("🔍 Debug finalizado")

