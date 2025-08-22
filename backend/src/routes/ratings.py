from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.database import db
from src.models.station_rating import StationRating
from src.models.price_rating import PriceRating
from src.models.gas_station import GasStation, FuelPrice
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

ratings_bp = Blueprint('ratings', __name__, url_prefix='/api')

@ratings_bp.route('/stations/<int:station_id>/ratings', methods=['POST'])
@jwt_required()
def submit_station_rating(station_id):
    """Submit a rating for a specific gas station."""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'rating' not in data:
        return jsonify({'success': False, 'error': 'Dados de avaliação ausentes.'}), 400

    rating_value = data.get('rating')
    comment = data.get('comment')

    if not isinstance(rating_value, int) or not 1 <= rating_value <= 5:
        return jsonify({'success': False, 'error': 'A avaliação deve ser um número inteiro entre 1 e 5.'}), 400

    if not GasStation.query.get(station_id):
        return jsonify({'success': False, 'error': 'Posto de combustível não encontrado.'}), 404

    # Verificar se o usuário já avaliou este posto
    existing_rating = StationRating.query.filter_by(user_id=current_user_id, station_id=station_id).first()
    if existing_rating:
        return jsonify({'success': False, 'error': 'Você já avaliou este posto.'}), 409 # Conflict

    try:
        new_rating = StationRating(
            user_id=current_user_id,
            station_id=station_id,
            rating=rating_value,
            comment=comment
        )
        db.session.add(new_rating)
        db.session.commit()

        # Atualizar a avaliação média do posto
        station = GasStation.query.get(station_id)
        if station:
            station.update_average_rating()

        return jsonify({'success': True, 'message': 'Avaliação enviada com sucesso.', 'data': new_rating.to_dict()}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro de integridade do banco de dados.'}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao submeter avaliação do posto: {e}")
        return jsonify({'success': False, 'error': 'Ocorreu um erro interno.'}), 500

@ratings_bp.route('/prices/<int:price_id>/ratings', methods=['POST'])
@jwt_required()
def submit_price_rating(price_id):
    """Submit a validation for a specific fuel price."""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({'success': False, 'error': 'Status de validação ausente.'}), 400

    status = data.get('status')
    valid_statuses = ['correct', 'incorrect', 'outdated']
    if status not in valid_statuses:
        return jsonify({'success': False, 'error': f'Status inválido. Use um de: {valid_statuses}'}), 400

    price = FuelPrice.query.get(price_id)
    if not price:
        return jsonify({'success': False, 'error': 'Preço não encontrado.'}), 404

    # Verificar se o usuário já validou este preço recentemente
    existing_validation = PriceRating.query.filter_by(user_id=current_user_id, price_id=price_id).first()
    if existing_validation:
        # Opcional: permitir atualizar a validação
        # existing_validation.status = status
        # existing_validation.validated_at = datetime.now(timezone.utc)
        # db.session.commit()
        # return jsonify({'success': True, 'message': 'Validação atualizada com sucesso.'}), 200
        return jsonify({'success': False, 'error': 'Você já validou este preço.'}), 409 # Conflict

    try:
        new_validation = PriceRating(
            user_id=current_user_id,
            price_id=price_id,
            status=status
        )
        db.session.add(new_validation)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Validação de preço enviada com sucesso.', 'data': new_validation.to_dict()}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro de integridade do banco de dados.'}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao validar preço: {e}")
        return jsonify({'success': False, 'error': 'Ocorreu um erro interno.'}), 500
