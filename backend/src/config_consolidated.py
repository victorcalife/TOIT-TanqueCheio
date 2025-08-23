import os
from datetime import timedelta

class Config:
    """Base configuration with default settings."""
    
    # Core Settings
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
        'postgresql://postgres:HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL@postgres-admt.railway.internal:5432/railway')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 10,
        'pool_size': 20
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'aouH&9sa&a86dsha*A6doishaoisjao')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 24)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 30)))
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://default:RxEKdfxmBpTrfniWWjMCfdvQOWTrmeFB@nozomi.proxy.rlwy.net:16784')
    
    # Session Configuration
    SESSION_SECRET = os.environ.get('SESSION_SECRET', 'tanque-cheio-session-secret')
    
    # API Configuration
    API_URL = os.environ.get('API_URL', 'https://betc-production.up.railway.app/api')
    NODE_ENV = os.environ.get('NODE_ENV', 'production')
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


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Enforce production security
    if not Config.SECRET_KEY or Config.SECRET_KEY == 'default-secret-key-for-dev':
        raise ValueError("SECRET_KEY must be set in production")
    if not Config.JWT_SECRET_KEY or Config.JWT_SECRET_KEY == 'default-jwt-secret-for-dev':
        raise ValueError("JWT_SECRET_KEY must be set in production")


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}


def get_config():
    """Get configuration based on environment.
    
    Returns:
        Config: The configuration class for the current environment.
    """
    env = os.environ.get('FLASK_ENV', 'production')
    return config.get(env, config['default'])


def config_by_name(config_name):
    """Get configuration by name.
    
    Args:
        config_name (str): Name of the configuration ('development', 'production', 'testing')
        
    Returns:
        Config: The requested configuration class
        
    Raises:
        ValueError: If the config_name is not found
    """
    config_class = config.get(config_name)
    if not config_class:
        raise ValueError(f"Unknown configuration: {config_name}")
    return config_class
