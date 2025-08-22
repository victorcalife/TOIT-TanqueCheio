import pytest
from src.main import create_app
from src.database import db as _db

@pytest.fixture(scope='session')
def app():
    """Cria uma instância da aplicação Flask para a sessão de testes."""
    # Força a configuração de teste
    app = create_app(config_name='test')
    
    # Estabelece um contexto de aplicação
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    """Fixture do banco de dados para a sessão de testes."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Cria uma nova sessão de banco de dados para cada teste."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture()
def client(app):
    """Um cliente de teste para a aplicação."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """Um executor de teste para a CLI do Flask."""
    return app.test_cli_runner()
