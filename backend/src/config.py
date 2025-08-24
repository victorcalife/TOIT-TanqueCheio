import os

class Config:
    """Configurações base."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:HXmzPSGlMEcjpzICIZphyTFuNLcGbAjL@postgres-admt.railway.internal:5432/railway')
    # Garante que as chaves secretas sejam definidas em produção
    if not Config.SECRET_KEY or Config.SECRET_KEY == ("SECRET_KEY"):
        raise ValueError("SECRET_KEY")
    if not Config.JWT_SECRET_KEY or Config.JWT_SECRET_KEY == ("JWT_SECRET_KEY"):
        raise ValueError("JWT_SECRET_KEY")

# Mapeamento para facilitar a seleção da configuração
config_by_name = dict(
        production=ProductionConfig
)
