import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

class PriceIntelligenceService:
    """Serviço de inteligência de preços com análise preditiva"""
    
    def __init__(self):
        self.price_history = {}  # station_id -> [price_records]
        self.market_trends = {}  # fuel_type -> trend_data
        self.price_predictions = {}  # station_id -> predictions
        self.regional_averages = {}  # region -> fuel_type -> average
        
        # Inicializar com dados simulados
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Inicializar com dados de exemplo para demonstração"""
        
        # Dados históricos simulados para diferentes postos
        stations_data = {
            'shell_br101': {
                'name': 'Posto Shell BR-101',
                'brand': 'Shell',
                'region': 'sul_brasil',
                'gasoline_history': [5.89, 5.85, 5.92, 5.88, 5.75, 5.79, 5.82],
                'ethanol_history': [4.29, 4.25, 4.32, 4.28, 4.15, 4.19, 4.22],
                'diesel_history': [5.65, 5.62, 5.68, 5.64, 5.55, 5.58, 5.61]
            },
            'petrobras_itajai': {
                'name': 'Petrobras Itajaí',
                'brand': 'Petrobras',
                'region': 'sul_brasil',
                'gasoline_history': [5.75, 5.72, 5.78, 5.74, 5.69, 5.71, 5.73],
                'ethanol_history': [4.15, 4.12, 4.18, 4.14, 4.09, 4.11, 4.13],
                'diesel_history': [5.55, 5.52, 5.58, 5.54, 5.49, 5.51, 5.53]
            },
            'ipiranga_centro': {
                'name': 'Ipiranga Centro',
                'brand': 'Ipiranga',
                'region': 'sul_brasil',
                'gasoline_history': [5.69, 5.66, 5.72, 5.68, 5.63, 5.65, 5.67],
                'ethanol_history': [4.09, 4.06, 4.12, 4.08, 4.03, 4.05, 4.07],
                'diesel_history': [5.49, 5.46, 5.52, 5.48, 5.43, 5.45, 5.47]
            }
        }
        
        # Processar dados históricos
        for station_id, data in stations_data.items():
            self.price_history[station_id] = []
            
            # Criar histórico dos últimos 7 dias
            for i, (gas_price, eth_price, diesel_price) in enumerate(zip(
                data['gasoline_history'], data['ethanol_history'], data['diesel_history']
            )):
                date = datetime.now() - timedelta(days=6-i)
                
                self.price_history[station_id].append({
                    'date': date.isoformat(),
                    'gasoline': gas_price,
                    'ethanol': eth_price,
                    'diesel': diesel_price,
                    'diesel_s10': diesel_price + 0.10,
                    'gnv': diesel_price - 0.70
                })
        
        # Calcular médias regionais
        self._calculate_regional_averages()
        
        # Calcular tendências de mercado
        self._calculate_market_trends()
    
    def _calculate_regional_averages(self):
        """Calcular médias regionais de preços"""
        regions = {}
        
        for station_id, history in self.price_history.items():
            if not history:
                continue
                
            # Assumir região sul_brasil para todos os postos de exemplo
            region = 'sul_brasil'
            
            if region not in regions:
                regions[region] = {'gasoline': [], 'ethanol': [], 'diesel': [], 'diesel_s10': [], 'gnv': []}
            
            # Usar preço mais recente
            latest_prices = history[-1]
            regions[region]['gasoline'].append(latest_prices['gasoline'])
            regions[region]['ethanol'].append(latest_prices['ethanol'])
            regions[region]['diesel'].append(latest_prices['diesel'])
            regions[region]['diesel_s10'].append(latest_prices['diesel_s10'])
            regions[region]['gnv'].append(latest_prices['gnv'])
        
        # Calcular médias
        for region, fuel_prices in regions.items():
            self.regional_averages[region] = {}
            for fuel_type, prices in fuel_prices.items():
                if prices:
                    self.regional_averages[region][fuel_type] = {
                        'average': round(statistics.mean(prices), 2),
                        'min': round(min(prices), 2),
                        'max': round(max(prices), 2),
                        'median': round(statistics.median(prices), 2)
                    }
    
    def _calculate_market_trends(self):
        """Calcular tendências de mercado"""
        fuel_types = ['gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv']
        
        for fuel_type in fuel_types:
            prices_over_time = []
            
            # Coletar preços ao longo do tempo
            for station_id, history in self.price_history.items():
                for record in history:
                    prices_over_time.append({
                        'date': record['date'],
                        'price': record[fuel_type]
                    })
            
            if len(prices_over_time) < 2:
                continue
            
            # Ordenar por data
            prices_over_time.sort(key=lambda x: x['date'])
            
            # Calcular tendência (simples: comparar primeiro e último)
            first_price = prices_over_time[0]['price']
            last_price = prices_over_time[-1]['price']
            
            trend = 'stable'
            change_percent = 0
            
            if last_price > first_price * 1.02:  # Aumento > 2%
                trend = 'rising'
                change_percent = ((last_price - first_price) / first_price) * 100
            elif last_price < first_price * 0.98:  # Diminuição > 2%
                trend = 'falling'
                change_percent = ((last_price - first_price) / first_price) * 100
            
            self.market_trends[fuel_type] = {
                'trend': trend,
                'change_percent': round(change_percent, 2),
                'current_average': round(statistics.mean([p['price'] for p in prices_over_time[-3:]]), 2),
                'volatility': self._calculate_volatility([p['price'] for p in prices_over_time])
            }
    
    def _calculate_volatility(self, prices: List[float]) -> str:
        """Calcular volatilidade dos preços"""
        if len(prices) < 2:
            return 'unknown'
        
        std_dev = statistics.stdev(prices)
        mean_price = statistics.mean(prices)
        
        coefficient_variation = (std_dev / mean_price) * 100
        
        if coefficient_variation < 1:
            return 'low'
        elif coefficient_variation < 3:
            return 'medium'
        else:
            return 'high'
    
    def predict_price_trend(self, station_id: str, fuel_type: str, days_ahead: int = 7) -> Dict:
        """Prever tendência de preços para os próximos dias"""
        
        if station_id not in self.price_history:
            return {'error': 'Posto não encontrado no histórico'}
        
        history = self.price_history[station_id]
        if not history:
            return {'error': 'Sem dados históricos suficientes'}
        
        # Extrair preços do combustível específico
        prices = [record[fuel_type] for record in history]
        
        if len(prices) < 3:
            return {'error': 'Dados insuficientes para previsão'}
        
        # Análise simples de tendência
        recent_prices = prices[-3:]  # Últimos 3 registros
        trend_slope = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
        
        # Gerar previsões
        predictions = []
        current_price = prices[-1]
        
        for day in range(1, days_ahead + 1):
            # Aplicar tendência com alguma variação aleatória
            predicted_price = current_price + (trend_slope * day)
            
            # Adicionar variação aleatória pequena (±2%)
            variation = random.uniform(-0.02, 0.02)
            predicted_price *= (1 + variation)
            
            predictions.append({
                'day': day,
                'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                'predicted_price': round(predicted_price, 2),
                'confidence': max(0.6, 0.9 - (day * 0.05))  # Confiança diminui com o tempo
            })
        
        # Análise da tendência
        if trend_slope > 0.01:
            trend_analysis = 'rising'
            trend_description = 'Preços em tendência de alta'
        elif trend_slope < -0.01:
            trend_analysis = 'falling'
            trend_description = 'Preços em tendência de baixa'
        else:
            trend_analysis = 'stable'
            trend_description = 'Preços estáveis'
        
        return {
            'station_id': station_id,
            'fuel_type': fuel_type,
            'current_price': prices[-1],
            'trend_analysis': trend_analysis,
            'trend_description': trend_description,
            'predictions': predictions,
            'recommendation': self._generate_recommendation(trend_analysis, prices[-1])
        }
    
    def _generate_recommendation(self, trend: str, current_price: float) -> Dict:
        """Gerar recomendação baseada na tendência"""
        
        if trend == 'rising':
            return {
                'action': 'buy_now',
                'message': 'Recomendamos abastecer agora, preços podem subir',
                'urgency': 'high',
                'icon': '⬆️'
            }
        elif trend == 'falling':
            return {
                'action': 'wait',
                'message': 'Considere aguardar, preços podem cair',
                'urgency': 'low',
                'icon': '⬇️'
            }
        else:
            return {
                'action': 'neutral',
                'message': 'Preços estáveis, momento neutro para abastecer',
                'urgency': 'medium',
                'icon': '➡️'
            }
    
    def find_best_price_opportunity(self, fuel_type: str, max_distance: float = 10.0) -> Dict:
        """Encontrar melhor oportunidade de preço na região"""
        
        opportunities = []
        
        for station_id, history in self.price_history.items():
            if not history:
                continue
            
            latest_record = history[-1]
            current_price = latest_record[fuel_type]
            
            # Calcular se é uma boa oportunidade
            regional_avg = self.regional_averages.get('sul_brasil', {}).get(fuel_type, {}).get('average', current_price)
            
            savings_percent = ((regional_avg - current_price) / regional_avg) * 100
            
            if savings_percent > 1:  # Economia > 1%
                # Simular distância (em produção viria do GPS)
                distance = random.uniform(1.0, max_distance)
                
                opportunities.append({
                    'station_id': station_id,
                    'station_name': self._get_station_name(station_id),
                    'current_price': current_price,
                    'regional_average': regional_avg,
                    'savings_percent': round(savings_percent, 2),
                    'savings_per_liter': round(regional_avg - current_price, 2),
                    'distance': round(distance, 1),
                    'score': self._calculate_opportunity_score(savings_percent, distance)
                })
        
        # Ordenar por score (melhor oportunidade primeiro)
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        if not opportunities:
            return {
                'found': False,
                'message': 'Nenhuma oportunidade especial encontrada no momento'
            }
        
        best_opportunity = opportunities[0]
        
        return {
            'found': True,
            'best_opportunity': best_opportunity,
            'all_opportunities': opportunities[:5],  # Top 5
            'message': f"💰 Economia de {best_opportunity['savings_percent']:.1f}% encontrada!"
        }
    
    def _get_station_name(self, station_id: str) -> str:
        """Obter nome do posto pelo ID"""
        names = {
            'shell_br101': 'Posto Shell BR-101',
            'petrobras_itajai': 'Petrobras Itajaí',
            'ipiranga_centro': 'Ipiranga Centro'
        }
        return names.get(station_id, f'Posto {station_id}')
    
    def _calculate_opportunity_score(self, savings_percent: float, distance: float) -> float:
        """Calcular score da oportunidade (economia vs distância)"""
        # Score baseado em economia vs distância
        # Economia alta + distância baixa = score alto
        distance_penalty = distance / 10.0  # Penalidade por distância
        return max(0, savings_percent - distance_penalty)
    
    def get_market_insights(self, fuel_type: str) -> Dict:
        """Obter insights do mercado para um tipo de combustível"""
        
        if fuel_type not in self.market_trends:
            return {'error': f'Dados não disponíveis para {fuel_type}'}
        
        trend_data = self.market_trends[fuel_type]
        regional_data = self.regional_averages.get('sul_brasil', {}).get(fuel_type, {})
        
        # Gerar insights inteligentes
        insights = []
        
        if trend_data['trend'] == 'rising':
            insights.append({
                'type': 'warning',
                'message': f"Preços de {fuel_type} em alta ({trend_data['change_percent']:+.1f}%)",
                'icon': '📈'
            })
        elif trend_data['trend'] == 'falling':
            insights.append({
                'type': 'positive',
                'message': f"Preços de {fuel_type} em queda ({trend_data['change_percent']:+.1f}%)",
                'icon': '📉'
            })
        
        if trend_data['volatility'] == 'high':
            insights.append({
                'type': 'info',
                'message': f"Alta volatilidade nos preços de {fuel_type}",
                'icon': '⚡'
            })
        
        # Comparação com média regional
        if regional_data:
            price_range = regional_data['max'] - regional_data['min']
            insights.append({
                'type': 'info',
                'message': f"Variação regional: R$ {price_range:.2f} por litro",
                'icon': '📊'
            })
        
        return {
            'fuel_type': fuel_type,
            'market_trend': trend_data,
            'regional_stats': regional_data,
            'insights': insights,
            'last_updated': datetime.now().isoformat()
        }
    
    def analyze_user_savings(self, user_id: str, fuel_consumption: float, fuel_type: str) -> Dict:
        """Analisar potencial de economia do usuário"""
        
        regional_data = self.regional_averages.get('sul_brasil', {}).get(fuel_type, {})
        
        if not regional_data:
            return {'error': 'Dados regionais não disponíveis'}
        
        # Calcular economia potencial
        avg_price = regional_data['average']
        min_price = regional_data['min']
        max_price = regional_data['max']
        
        # Economia mensal (assumindo consumo mensal)
        monthly_savings_min = (avg_price - min_price) * fuel_consumption
        monthly_savings_max = (max_price - min_price) * fuel_consumption
        
        # Economia anual
        annual_savings_min = monthly_savings_min * 12
        annual_savings_max = monthly_savings_max * 12
        
        return {
            'user_id': user_id,
            'fuel_type': fuel_type,
            'monthly_consumption': fuel_consumption,
            'price_analysis': {
                'regional_average': avg_price,
                'best_price': min_price,
                'worst_price': max_price,
                'price_range': round(max_price - min_price, 2)
            },
            'savings_potential': {
                'monthly_min': round(monthly_savings_min, 2),
                'monthly_max': round(monthly_savings_max, 2),
                'annual_min': round(annual_savings_min, 2),
                'annual_max': round(annual_savings_max, 2)
            },
            'recommendations': [
                {
                    'tip': 'Use o app para encontrar sempre os melhores preços',
                    'potential_saving': f'R$ {annual_savings_min:.0f} - R$ {annual_savings_max:.0f} por ano'
                },
                {
                    'tip': 'Configure notificações automáticas durante viagens',
                    'benefit': 'Economia automática sem esforço'
                },
                {
                    'tip': 'Monitore tendências de preços',
                    'benefit': 'Abasteça no momento ideal'
                }
            ]
        }
    
    def get_service_stats(self) -> Dict:
        """Obter estatísticas do serviço de inteligência"""
        return {
            'stations_monitored': len(self.price_history),
            'fuel_types_tracked': len(self.market_trends),
            'regions_covered': len(self.regional_averages),
            'total_price_records': sum(len(history) for history in self.price_history.values()),
            'last_updated': datetime.now().isoformat(),
            'service_status': 'operational'
        }

# Instância global do serviço
price_intelligence = PriceIntelligenceService()

def get_smart_recommendation(fuel_type: str, consumption: float, max_distance: float = 10.0) -> Dict:
    """Função helper para obter recomendação inteligente"""
    
    # Combinar análise de oportunidades com insights de mercado
    opportunities = price_intelligence.find_best_price_opportunity(fuel_type, max_distance)
    market_insights = price_intelligence.get_market_insights(fuel_type)
    
    return {
        'opportunities': opportunities,
        'market_insights': market_insights,
        'recommendation_score': 'high' if opportunities.get('found') else 'medium',
        'generated_at': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Teste do serviço de inteligência de preços
    print("🧠 Testando Serviço de Inteligência de Preços")
    
    # Teste 1: Previsão de preços
    prediction = price_intelligence.predict_price_trend('shell_br101', 'gasoline', 5)
    print(f"\n📈 Previsão de preços: {prediction}")
    
    # Teste 2: Melhor oportunidade
    opportunity = price_intelligence.find_best_price_opportunity('gasoline')
    print(f"\n💰 Melhor oportunidade: {opportunity}")
    
    # Teste 3: Insights de mercado
    insights = price_intelligence.get_market_insights('gasoline')
    print(f"\n📊 Insights de mercado: {insights}")
    
    # Teste 4: Análise de economia do usuário
    savings = price_intelligence.analyze_user_savings('user_123', 50.0, 'gasoline')
    print(f"\n💵 Análise de economia: {savings}")

