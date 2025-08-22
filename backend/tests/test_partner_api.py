import json
import pytest

# Marca todos os testes neste arquivo para usar a fixture 'init_database'
pytestmark = pytest.mark.usefixtures("init_database")


def test_update_price_success(client):
    """Testa a atualização de preço por um parceiro com sucesso."""
    headers = {
        'X-API-KEY': 'test-api-key',
        'Content-Type': 'application/json'
    }
    data = {'price': 5.55, 'fuel_type': 'gasoline'}
    response = client.post('/api/partner/stations/1/prices', data=json.dumps(data), headers=headers)
    json_data = response.get_json()

    assert response.status_code == 200
    assert json_data['success'] is True
    assert 'Preço atualizado com sucesso' in json_data['message']
    assert json_data['price']['new_price'] == 5.55

def test_update_price_no_api_key(client):
    """Testa a falha na atualização de preço sem uma chave de API."""
    data = {'price': 5.55, 'fuel_type': 'gasoline'}
    response = client.post('/api/partner/stations/1/prices', data=json.dumps(data), content_type='application/json')
    json_data = response.get_json()

    assert response.status_code == 401
    assert json_data['success'] is False
    assert 'Chave de API não fornecida' in json_data['error']

def test_update_price_invalid_api_key(client):
    """Testa a falha na atualização com uma chave de API inválida."""
    headers = {'X-API-KEY': 'invalid-key', 'Content-Type': 'application/json'}
    data = {'price': 5.55, 'fuel_type': 'gasoline'}
    response = client.post('/api/partner/stations/1/prices', data=json.dumps(data), headers=headers)
    json_data = response.get_json()

    assert response.status_code == 403
    assert json_data['success'] is False
    assert 'Chave de API inválida ou expirada' in json_data['error']

def test_update_price_unauthorized_station(client):
    """Testa a falha ao tentar atualizar um posto não associado ao parceiro."""
    headers = {'X-API-KEY': 'test-api-key', 'Content-Type': 'application/json'}
    data = {'price': 5.55, 'fuel_type': 'gasoline'}
    # Tenta atualizar o posto com ID 99 (não existe ou não pertence ao parceiro)
    response = client.post('/api/partner/stations/99/prices', data=json.dumps(data), headers=headers)
    json_data = response.get_json()

    assert response.status_code == 403
    assert json_data['success'] is False
    assert 'Parceiro não autorizado a atualizar este posto' in json_data['error']

def test_update_price_missing_data(client):
    """Testa a falha na atualização por falta de dados."""
    headers = {'X-API-KEY': 'test-api-key', 'Content-Type': 'application/json'}
    # Faltando 'price'
    data = {'fuel_type': 'gasoline'}
    response = client.post('/api/partner/stations/1/prices', data=json.dumps(data), headers=headers)
    json_data = response.get_json()

    assert response.status_code == 400
    assert json_data['success'] is False
    assert 'Dados incompletos' in json_data['error']
