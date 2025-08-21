#!/usr/bin/env python3
"""
Script para popular banco de dados com dados de exemplo
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.database import db
from src.models.gas_station import GasStation, FuelPrice
from src.models.partner import Partner
from src.models.coupon import Coupon
import random
from datetime import datetime, timedelta

def populate_sample_data():
    app = create_app()
    
    with app.app_context():
        # Limpar dados existentes
        FuelPrice.query.delete()
        Coupon.query.delete()
        GasStation.query.delete()
        Partner.query.delete()
        
        # Criar parceiros
        partners = [
            Partner(
                name="Petrobras",
                contact_email="parceria@petrobras.com.br",
                commission_rate=1.5,
                is_active=True
            ),
            Partner(
                name="Shell",
                contact_email="parceria@shell.com.br", 
                commission_rate=2.0,
                is_active=True
            ),
            Partner(
                name="Ipiranga",
                contact_email="parceria@ipiranga.com.br",
                commission_rate=1.8,
                is_active=True
            ),
            Partner(
                name="Ale",
                contact_email="parceria@ale.com.br",
                commission_rate=2.2,
                is_active=True
            )
        ]
        
        for partner in partners:
            db.session.add(partner)
        
        db.session.commit()
        
        # Postos em São Paulo e região
        gas_stations_data = [
            # São Paulo Centro
            {"name": "Posto Petrobras Centro", "brand": "Petrobras", "lat": -23.5505, "lng": -46.6333, "address": "Av. Paulista, 1000 - Bela Vista, São Paulo - SP"},
            {"name": "Shell Select Paulista", "brand": "Shell", "lat": -23.5615, "lng": -46.6565, "address": "Av. Paulista, 2000 - Cerqueira César, São Paulo - SP"},
            {"name": "Ipiranga Vila Madalena", "brand": "Ipiranga", "lat": -23.5448, "lng": -46.6918, "address": "R. Harmonia, 500 - Vila Madalena, São Paulo - SP"},
            
            # Zona Sul
            {"name": "Posto Ale Moema", "brand": "Ale", "lat": -23.5928, "lng": -46.6648, "address": "Av. Ibirapuera, 1500 - Moema, São Paulo - SP"},
            {"name": "Shell Vila Olímpia", "brand": "Shell", "lat": -23.5955, "lng": -46.6890, "address": "Av. Faria Lima, 3000 - Vila Olímpia, São Paulo - SP"},
            {"name": "Petrobras Brooklin", "brand": "Petrobras", "lat": -23.6108, "lng": -46.7025, "address": "Av. Santo Amaro, 2500 - Brooklin, São Paulo - SP"},
            
            # Zona Norte
            {"name": "Ipiranga Santana", "brand": "Ipiranga", "lat": -23.5033, "lng": -46.6291, "address": "Av. Cruzeiro do Sul, 1000 - Santana, São Paulo - SP"},
            {"name": "Posto Ale Tucuruvi", "brand": "Ale", "lat": -23.4708, "lng": -46.6058, "address": "Av. Nova Cantareira, 800 - Tucuruvi, São Paulo - SP"},
            
            # Zona Leste
            {"name": "Shell Tatuapé", "brand": "Shell", "lat": -23.5403, "lng": -46.5768, "address": "R. Tuiuti, 2000 - Tatuapé, São Paulo - SP"},
            {"name": "Petrobras Penha", "brand": "Petrobras", "lat": -23.5273, "lng": -46.5408, "address": "Av. Celso Garcia, 3000 - Penha, São Paulo - SP"},
            
            # Zona Oeste
            {"name": "Ipiranga Pinheiros", "brand": "Ipiranga", "lat": -23.5648, "lng": -46.7018, "address": "R. Teodoro Sampaio, 1500 - Pinheiros, São Paulo - SP"},
            {"name": "Ale Butantã", "brand": "Ale", "lat": -23.5708, "lng": -46.7298, "address": "Av. Vital Brasil, 1000 - Butantã, São Paulo - SP"},
            
            # Grande São Paulo
            {"name": "Shell Osasco", "brand": "Shell", "lat": -23.5325, "lng": -46.7918, "address": "Av. dos Autonomistas, 2000 - Osasco, SP"},
            {"name": "Petrobras Santo André", "brand": "Petrobras", "lat": -23.6628, "lng": -46.5308, "address": "Av. Industrial, 1500 - Santo André, SP"},
            {"name": "Ipiranga Guarulhos", "brand": "Ipiranga", "lat": -23.4628, "lng": -46.5338, "address": "Av. Monteiro Lobato, 3000 - Guarulhos, SP"},
            
            # Rodovias
            {"name": "Shell Rodovia Anhanguera", "brand": "Shell", "lat": -23.4108, "lng": -46.7708, "address": "Rod. Anhanguera, Km 25 - Perus, São Paulo - SP"},
            {"name": "Petrobras Via Dutra", "brand": "Petrobras", "lat": -23.3608, "lng": -46.3108, "address": "Rod. Presidente Dutra, Km 200 - Guarulhos, SP"},
            {"name": "Ipiranga Rodovia Imigrantes", "brand": "Ipiranga", "lat": -23.7108, "lng": -46.6408, "address": "Rod. dos Imigrantes, Km 15 - São Bernardo do Campo, SP"},
        ]
        
        stations = []
        for data in gas_stations_data:
            partner = Partner.query.filter_by(name=data["brand"]).first()
            station = GasStation(
                name=data["name"],
                brand=data["brand"],
                address=data["address"],
                latitude=data["lat"],
                longitude=data["lng"],
                phone=f"+55 11 {random.randint(90000, 99999)}-{random.randint(1000, 9999)}",
                is_active=True,
                partner_id=partner.id if partner else None
            )
            stations.append(station)
            db.session.add(station)
        
        db.session.commit()
        
        # Adicionar preços de combustível
        fuel_types = ['gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv']
        base_prices = {
            'gasoline': 5.89,
            'ethanol': 4.29,
            'diesel': 6.15,
            'diesel_s10': 6.25,
            'gnv': 4.89
        }
        
        for station in stations:
            for fuel_type in fuel_types:
                # Variação de preço por posto (-10% a +15%)
                variation = random.uniform(-0.10, 0.15)
                price = base_prices[fuel_type] * (1 + variation)
                price = round(price, 2)
                
                fuel_price = FuelPrice(
                    gas_station_id=station.id,
                    fuel_type=fuel_type,
                    price=price,
                    last_updated=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                )
                db.session.add(fuel_price)
        
        # Adicionar cupons
        coupons_data = [
            {"station_name": "Shell Select Paulista", "discount": 0.15, "fuel": "gasoline", "desc": "15 centavos de desconto na gasolina"},
            {"station_name": "Posto Petrobras Centro", "discount": 0.10, "fuel": "ethanol", "desc": "10 centavos de desconto no etanol"},
            {"station_name": "Ipiranga Vila Madalena", "discount": 0.20, "fuel": "diesel_s10", "desc": "20 centavos de desconto no diesel S10"},
            {"station_name": "Shell Vila Olímpia", "discount": 0.12, "fuel": "gasoline", "desc": "12 centavos de desconto na gasolina"},
            {"station_name": "Posto Ale Moema", "discount": 0.08, "fuel": "gnv", "desc": "8 centavos de desconto no GNV"},
        ]
        
        for coupon_data in coupons_data:
            station = GasStation.query.filter_by(name=coupon_data["station_name"]).first()
            if station:
                coupon = Coupon(
                    gas_station_id=station.id,
                    title=f"Desconto {coupon_data['desc']}",
                    description=coupon_data['desc'],
                    discount_type='fixed',
                    discount_value=coupon_data['discount'],
                    fuel_type=coupon_data['fuel'],
                    valid_from=datetime.utcnow(),
                    valid_until=datetime.utcnow() + timedelta(days=30),
                    is_active=True,
                    usage_limit=1000,
                    usage_count=random.randint(10, 100)
                )
                db.session.add(coupon)
        
        db.session.commit()
        
        print(f"✅ Dados populados com sucesso!")
        print(f"   - {len(partners)} parceiros")
        print(f"   - {len(stations)} postos de combustível") 
        print(f"   - {len(stations) * len(fuel_types)} preços de combustível")
        print(f"   - {len(coupons_data)} cupons de desconto")

if __name__ == "__main__":
    populate_sample_data()

