import os
from datetime import timedelta

class Config:
    """Configuração base da aplicação"""
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:WWyaQJVrqJqmryQNcKdIyQBjGsPIbsXJ@interchange.proxy.rlwy.net:16420/railway')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'tanque-cheio-secret-2025')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 24)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 30)))
    
    # Redis Configuration (opcional)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://default:RxEKdfxmBpTrfniWWjMCfdvQOWTrmeFB@nozomi.proxy.rlwy.net:16784')
    
    # Session Configuration
    SESSION_SECRET = os.environ.get('SESSION_SECRET', 'tanque-cheio-session-secret')
    
    # API Configuration
    API_URL = os.environ.get('API_URL', 'localhost:8080')
    NODE_ENV = os.environ.get('NODE_ENV', 'development')
    PORT = int(os.environ.get('PORT', 8080))
    
    # Google Maps API
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60))
    RATE_LIMIT_PER_HOUR = int(os.environ.get('RATE_LIMIT_PER_HOUR', 1000))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    
    # Security
    BCRYPT_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', 12))
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    
    # Notification Settings
    NOTIFICATION_BATCH_SIZE = int(os.environ.get('NOTIFICATION_BATCH_SIZE', 100))
    NOTIFICATION_RETRY_ATTEMPTS = int(os.environ.get('NOTIFICATION_RETRY_ATTEMPTS', 3))
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    TESTING = False
    
    # Configurações específicas de produção
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 10,
        'pool_size': 20
    }

class TestingConfig(Config):
    """Configuração para testes"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuração baseada no ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Retorna a configuração baseada no ambiente"""
    env = os.environ.get('NODE_ENV', 'development')
    return config.get(env, config['default'])

