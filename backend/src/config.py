import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Session
    SECRET_KEY = os.getenv('SESSION_SECRET', 'dev-session-secret')
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'tanque_cheio:'
    
    # API
    API_URL = os.getenv('API_URL', 'localhost:8080')
    PORT = int(os.getenv('PORT', 8080))
    
    # Google Maps
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
    
    # Security
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', 12))
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # Notifications
    NOTIFICATION_BATCH_SIZE = int(os.getenv('NOTIFICATION_BATCH_SIZE', 100))
    NOTIFICATION_RETRY_ATTEMPTS = int(os.getenv('NOTIFICATION_RETRY_ATTEMPTS', 3))
    
    # CORS
    CORS_ORIGINS = ['*']  # Allow all origins in development
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production database URL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Production Redis URL
    REDIS_URL = os.getenv('REDIS_URL')
    
    # Stricter CORS in production
    CORS_ORIGINS = [
        'https://fetc-production.up.railway.app',
        'https://frontend-tc-development.up.railway.app'
    ]

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    BCRYPT_ROUNDS = 4  # Faster for tests

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

