import json

# Marca todos os testes neste arquivo para usar a fixture 'init_database'
pytestmark = pytest.mark.usefixtures("init_database")


def test_submit_station_rating_success(client, auth_headers):
    """Testa o envio de uma avaliação de posto com sucesso."""
    data = {'station_id': 1, 'rating': 5, 'comment': 'Ótimo atendimento!'}
    response = client.post('/api/ratings/station', data=json.dumps(data), headers=auth_headers, content_type='application/json')
    json_data = response.get_json()

    assert response.status_code == 201
    assert json_data['success'] is True
    assert 'Avaliação registrada com sucesso' in json_data['message']
    assert json_data['rating']['station_id'] == 1
    assert json_data['rating']['rating'] == 5

def test_submit_price_validation_success(client, auth_headers):
    """Testa o envio de uma validação de preço com sucesso."""
    data = {'price_id': 1, 'status': 'correct'}
    response = client.post('/api/ratings/price', data=json.dumps(data), headers=auth_headers, content_type='application/json')
    json_data = response.get_json()

    assert response.status_code == 201
    assert json_data['success'] is True
    assert 'Validação de preço registrada com sucesso' in json_data['message']
    assert json_data['rating']['price_id'] == 1
    assert json_data['rating']['status'] == 'correct'

def test_submit_rating_unauthorized(client):
    """Testa que um usuário não autenticado não pode enviar avaliações."""
    data = {'station_id': 1, 'rating': 5}
    response = client.post('/api/ratings/station', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 401 # Unauthorized

def test_duplicate_station_rating_fails(client, auth_headers):
    """Testa que um usuário não pode avaliar o mesmo posto duas vezes."""
    # Primeira avaliação (deve funcionar)
    data = {'station_id': 1, 'rating': 4}
    client.post('/api/ratings/station', data=json.dumps(data), headers=auth_headers, content_type='application/json')

    # Segunda avaliação (deve falhar)
    data2 = {'station_id': 1, 'rating': 3}
    response = client.post('/api/ratings/station', data=json.dumps(data2), headers=auth_headers, content_type='application/json')
    json_data = response.get_json()

    assert response.status_code == 409 # Conflict
    assert json_data['success'] is False
    assert 'Você já avaliou este posto' in json_data['error']

def test_duplicate_price_validation_fails(client, auth_headers):
    """Testa que um usuário não pode validar o mesmo preço duas vezes."""
    # Primeira validação
    data = {'price_id': 1, 'status': 'incorrect'}
    client.post('/api/ratings/price', data=json.dumps(data), headers=auth_headers, content_type='application/json')

    # Segunda validação
    data2 = {'price_id': 1, 'status': 'correct'}
    response = client.post('/api/ratings/price', data=json.dumps(data2), headers=auth_headers, content_type='application/json')
    json_data = response.get_json()

    assert response.status_code == 409 # Conflict
    assert json_data['success'] is False
    assert 'Você já validou este preço' in json_data['error']

def test_missing_rating_data_fails(client, auth_headers):
    """Testa a falha ao enviar dados de avaliação incompletos."""
    # Faltando 'rating'
    data = {'station_id': 1, 'comment': 'Faltou a nota'}
    response = client.post('/api/ratings/station', data=json.dumps(data), headers=auth_headers, content_type='application/json')
    assert response.status_code == 400 # Bad Request

    # Faltando 'station_id'
    data2 = {'rating': 5, 'comment': 'Faltou o posto'}
    response2 = client.post('/api/ratings/station', data=json.dumps(data2), headers=auth_headers, content_type='application/json')
    assert response2.status_code == 400 # Bad Request
