from flask import Blueprint, request, jsonify, g
from functools import wraps
from src.database import db
from src.models.partner import Partner
from src.models.gas_station import GasStation, FuelPrice
from datetime import datetime, timezone

partner_api_bp = Blueprint('partner_api', __name__, url_prefix='/api/partner')

# --- Decorator para Autenticação por API Key ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'success': False, 'error': 'Chave de API ausente no cabeçalho X-API-Key.'}), 401

        partner = Partner.find_by_api_key(api_key)
        if not partner or not partner.is_api_key_valid():
            return jsonify({'success': False, 'error': 'Chave de API inválida ou expirada.'}), 403

        # Anexa o parceiro ao contexto global da requisição para uso posterior
        g.partner = partner
        return f(*args, **kwargs)
    return decorated_function

# --- Endpoint de Teste de Autenticação ---
@partner_api_bp.route('/auth-test', methods=['GET'])
@require_api_key
def auth_test():
    """Endpoint para que parceiros testem sua chave de API."""
    partner = g.partner
    return jsonify({
        'success': True,
        'message': 'Autenticação bem-sucedida.',
        'partner': {
            'id': partner.id,
            'company_name': partner.company_name
        }
    })

# --- Endpoint para Atualização de Preços ---
@partner_api_bp.route('/prices', methods=['POST'])
@require_api_key
def update_prices():
    """Permite que um parceiro atualize os preços de múltiplos combustíveis em múltiplos postos."""
    partner = g.partner
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({'success': False, 'error': 'O corpo da requisição deve ser uma lista de atualizações de preço.'}), 400

    partner_station_ids = {station.id for station in partner.gas_stations}
    updated_prices = []
    errors = []

    for item in data:
        station_id = item.get('station_id')
        fuel_type = item.get('fuel_type')
        price = item.get('price')

        # --- Validações ---
        if not all([station_id, fuel_type, price]):
            errors.append({'item': item, 'error': 'Campos station_id, fuel_type e price são obrigatórios.'})
            continue

        if station_id not in partner_station_ids:
            errors.append({'item': item, 'error': f'Acesso negado. O posto {station_id} não pertence a este parceiro.'})
            continue

        try:
            price = float(price)
            if price <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            errors.append({'item': item, 'error': 'O preço deve ser um número positivo.'})
            continue
        
        # --- Lógica de Atualização ---
        try:
            # Desativa o preço antigo, se houver
            FuelPrice.query.filter_by(gas_station_id=station_id, fuel_type=fuel_type, is_active=True).update({'is_active': False})

            # Cria o novo preço
            new_price = FuelPrice(
                gas_station_id=station_id,
                fuel_type=fuel_type,
                price=price,
                reported_by='partner',
                is_active=True,
                reported_at=datetime.now(timezone.utc)
            )
            db.session.add(new_price)
            updated_prices.append(new_price.to_dict())

        except Exception as e:
            db.session.rollback()
            errors.append({'item': item, 'error': f'Erro de banco de dados: {str(e)}'})
            # Se um falhar, paramos para evitar inconsistência parcial
            return jsonify({'success': False, 'error': 'Ocorreu um erro durante a transação.', 'details': errors}), 500

    if not errors:
        db.session.commit()
        return jsonify({'success': True, 'message': f'{len(updated_prices)} preços atualizados com sucesso.', 'data': updated_prices}), 200
    else:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Alguns itens continham erros e nenhuma alteração foi feita.', 'errors': errors}), 400
