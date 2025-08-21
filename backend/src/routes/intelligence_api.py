from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
import os

# Adicionar path para importar serviços
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.price_intelligence import price_intelligence, get_smart_recommendation

intelligence_bp = Blueprint('intelligence', __name__)

@intelligence_bp.route('/predict-prices', methods=['POST'])
@jwt_required()
def predict_prices():
    """API para previsão de preços"""
    try:
        data = request.get_json()
        
        station_id = data.get('station_id')
        fuel_type = data.get('fuel_type', 'gasoline')
        days_ahead = data.get('days_ahead', 7)
        
        if not station_id:
            return jsonify({
                'success': False,
                'error': 'station_id é obrigatório'
            }), 400
        
        prediction = price_intelligence.predict_price_trend(station_id, fuel_type, days_ahead)
        
        if 'error' in prediction:
            return jsonify({
                'success': False,
                'error': prediction['error']
            }), 404
        
        return jsonify({
            'success': True,
            'prediction': prediction
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/best-opportunities', methods=['GET'])
@jwt_required()
def get_best_opportunities():
    """API para encontrar melhores oportunidades de preço"""
    try:
        fuel_type = request.args.get('fuel_type', 'gasoline')
        max_distance = float(request.args.get('max_distance', 10.0))
        
        opportunities = price_intelligence.find_best_price_opportunity(fuel_type, max_distance)
        
        return jsonify({
            'success': True,
            'opportunities': opportunities
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/market-insights', methods=['GET'])
@jwt_required()
def get_market_insights():
    """API para insights de mercado"""
    try:
        fuel_type = request.args.get('fuel_type', 'gasoline')
        
        insights = price_intelligence.get_market_insights(fuel_type)
        
        if 'error' in insights:
            return jsonify({
                'success': False,
                'error': insights['error']
            }), 404
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/savings-analysis', methods=['POST'])
@jwt_required()
def analyze_savings():
    """API para análise de economia do usuário"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        fuel_consumption = data.get('fuel_consumption', 50.0)  # Litros por mês
        fuel_type = data.get('fuel_type', 'gasoline')
        
        analysis = price_intelligence.analyze_user_savings(user_id, fuel_consumption, fuel_type)
        
        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 404
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/smart-recommendation', methods=['POST'])
@jwt_required()
def get_smart_recommendation_api():
    """API para recomendação inteligente completa"""
    try:
        data = request.get_json()
        
        fuel_type = data.get('fuel_type', 'gasoline')
        consumption = data.get('consumption', 50.0)
        max_distance = data.get('max_distance', 10.0)
        
        recommendation = get_smart_recommendation(fuel_type, consumption, max_distance)
        
        return jsonify({
            'success': True,
            'recommendation': recommendation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/price-alerts', methods=['POST'])
@jwt_required()
def create_price_alert():
    """API para criar alerta de preço"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        fuel_type = data.get('fuel_type', 'gasoline')
        target_price = data.get('target_price')
        max_distance = data.get('max_distance', 10.0)
        
        if not target_price:
            return jsonify({
                'success': False,
                'error': 'target_price é obrigatório'
            }), 400
        
        # Verificar se já existe preço igual ou menor
        opportunities = price_intelligence.find_best_price_opportunity(fuel_type, max_distance)
        
        alert_triggered = False
        matching_stations = []
        
        if opportunities.get('found'):
            for opp in opportunities.get('all_opportunities', []):
                if opp['current_price'] <= target_price:
                    alert_triggered = True
                    matching_stations.append(opp)
        
        alert_data = {
            'user_id': user_id,
            'fuel_type': fuel_type,
            'target_price': target_price,
            'max_distance': max_distance,
            'alert_triggered': alert_triggered,
            'matching_stations': matching_stations,
            'created_at': price_intelligence.get_service_stats()['last_updated']
        }
        
        if alert_triggered:
            message = f"🚨 Alerta de preço ativado! Encontramos {len(matching_stations)} posto(s) com preço ≤ R$ {target_price:.2f}"
        else:
            message = f"⏰ Alerta criado! Você será notificado quando encontrarmos {fuel_type} por R$ {target_price:.2f} ou menos"
        
        return jsonify({
            'success': True,
            'alert': alert_data,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/regional-comparison', methods=['GET'])
@jwt_required()
def get_regional_comparison():
    """API para comparação regional de preços"""
    try:
        fuel_type = request.args.get('fuel_type', 'gasoline')
        
        # Obter dados regionais
        regional_data = price_intelligence.regional_averages.get('sul_brasil', {}).get(fuel_type, {})
        
        if not regional_data:
            return jsonify({
                'success': False,
                'error': 'Dados regionais não disponíveis'
            }), 404
        
        # Adicionar comparação com outras regiões (simulado)
        comparison_data = {
            'current_region': {
                'name': 'Sul do Brasil',
                'data': regional_data
            },
            'national_average': {
                'average': regional_data['average'] * 1.05,  # Simular média nacional 5% maior
                'comparison': 'Região 5% mais barata que a média nacional'
            },
            'nearby_regions': [
                {
                    'name': 'Sudeste',
                    'average': regional_data['average'] * 1.08,
                    'difference': f"+{((regional_data['average'] * 1.08 - regional_data['average']) / regional_data['average'] * 100):.1f}%"
                },
                {
                    'name': 'Centro-Oeste',
                    'average': regional_data['average'] * 0.97,
                    'difference': f"{((regional_data['average'] * 0.97 - regional_data['average']) / regional_data['average'] * 100):.1f}%"
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'fuel_type': fuel_type,
            'comparison': comparison_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/fuel-calculator', methods=['POST'])
@jwt_required()
def fuel_calculator():
    """API para calculadora de combustível inteligente"""
    try:
        data = request.get_json()
        
        distance = data.get('distance', 0)  # km
        fuel_efficiency = data.get('fuel_efficiency', 12)  # km/l
        fuel_type = data.get('fuel_type', 'gasoline')
        
        if distance <= 0:
            return jsonify({
                'success': False,
                'error': 'Distância deve ser maior que zero'
            }), 400
        
        # Calcular consumo
        fuel_needed = distance / fuel_efficiency
        
        # Obter preços regionais
        regional_data = price_intelligence.regional_averages.get('sul_brasil', {}).get(fuel_type, {})
        
        if not regional_data:
            return jsonify({
                'success': False,
                'error': 'Dados de preços não disponíveis'
            }), 404
        
        # Calcular custos
        cost_average = fuel_needed * regional_data['average']
        cost_best = fuel_needed * regional_data['min']
        cost_worst = fuel_needed * regional_data['max']
        
        # Calcular economia potencial
        potential_savings = cost_worst - cost_best
        
        calculation = {
            'trip_details': {
                'distance': distance,
                'fuel_efficiency': fuel_efficiency,
                'fuel_needed': round(fuel_needed, 2),
                'fuel_type': fuel_type
            },
            'cost_analysis': {
                'average_cost': round(cost_average, 2),
                'best_case_cost': round(cost_best, 2),
                'worst_case_cost': round(cost_worst, 2),
                'potential_savings': round(potential_savings, 2)
            },
            'price_breakdown': {
                'average_price': regional_data['average'],
                'best_price': regional_data['min'],
                'worst_price': regional_data['max'],
                'price_variation': round(regional_data['max'] - regional_data['min'], 2)
            },
            'recommendations': []
        }
        
        # Adicionar recomendações
        if potential_savings > 5:
            calculation['recommendations'].append({
                'type': 'savings',
                'message': f'Potencial de economia de R$ {potential_savings:.2f} escolhendo o posto certo',
                'icon': '💰'
            })
        
        if fuel_needed > 40:
            calculation['recommendations'].append({
                'type': 'planning',
                'message': 'Viagem longa detectada. Configure notificações automáticas no app',
                'icon': '🗺️'
            })
        
        return jsonify({
            'success': True,
            'calculation': calculation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/service-stats', methods=['GET'])
@jwt_required()
def get_service_stats():
    """API para estatísticas do serviço de inteligência"""
    try:
        stats = price_intelligence.get_service_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@intelligence_bp.route('/health', methods=['GET'])
def health_check():
    """Health check para o serviço de inteligência"""
    return jsonify({
        'success': True,
        'service': 'Price Intelligence API',
        'status': 'operational',
        'version': '1.0.0'
    })

