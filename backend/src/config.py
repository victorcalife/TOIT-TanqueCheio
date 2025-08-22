import os

class Config:
    """Configurações base."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-jwt-secret-for-dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL@postgres-admt.railway.internal:5432/railway')
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Configurações de teste."""
    TESTING = True
    # Usa um banco de dados SQLite em memória para testes rápidos e isolados
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # Desativa a proteção CSRF em testes para simplificar requisições
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Configurações de produção."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Garante que as chaves secretas sejam definidas em produção
    if not Config.SECRET_KEY or Config.SECRET_KEY == 'default-secret-key-for-dev':
        raise ValueError("SECRET_KEY não definida para produção.")
    if not Config.JWT_SECRET_KEY or Config.JWT_SECRET_KEY == 'default-jwt-secret-for-dev':
        raise ValueError("JWT_SECRET_KEY não definida para produção.")

# Mapeamento para facilitar a seleção da configuração
config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig
)
