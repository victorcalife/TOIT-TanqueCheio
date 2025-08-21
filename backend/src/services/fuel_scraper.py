import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional
from flask import current_app
from src.models.gas_station import GasStation, FuelPrice
from src.models.partner import Partner
from src.database import db
import time
import random

class FuelPriceScraper:
    """Service for scraping fuel prices from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_anp_prices(self, state: str = 'SP', city: str = None) -> List[Dict]:
        """Scrape fuel prices from ANP (Agência Nacional do Petróleo)"""
        try:
            # ANP API endpoint for fuel prices
            base_url = "https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos"
            
            # This is a simplified implementation
            # In reality, you would need to analyze the ANP website structure
            # and implement proper scraping logic
            
            current_app.logger.info(f"Scraping ANP prices for {state}/{city}")
            
            # Simulate API call (replace with actual implementation)
            prices = []
            
            # For now, return empty list as ANP requires specific implementation
            return prices
            
        except Exception as e:
            current_app.logger.error(f"ANP scraping error: {e}")
            return []
    
    def scrape_petrobras_prices(self) -> List[Dict]:
        """Scrape fuel prices from Petrobras website"""
        try:
            url = "https://petrobras.com.br/pt/nossas-atividades/precos-de-combustiveis/"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            prices = []
            
            # Look for price tables or sections
            price_sections = soup.find_all(['table', 'div'], class_=re.compile(r'price|combustivel|fuel', re.I))
            
            for section in price_sections:
                # Extract price information
                # This is a simplified implementation
                text = section.get_text()
                
                # Look for price patterns (R$ X,XX)
                price_matches = re.findall(r'R\$\s*(\d+[,\.]\d{2,3})', text)
                
                for price_match in price_matches:
                    price_value = float(price_match.replace(',', '.'))
                    
                    # Try to determine fuel type from context
                    fuel_type = self.detect_fuel_type(text)
                    
                    if fuel_type:
                        prices.append({
                            'source': 'petrobras_website',
                            'fuel_type': fuel_type,
                            'price': price_value,
                            'location': 'Brasil',
                            'confidence': 0.7,
                            'scraped_at': datetime.now(timezone.utc)
                        })
            
            current_app.logger.info(f"Scraped {len(prices)} prices from Petrobras")
            return prices
            
        except Exception as e:
            current_app.logger.error(f"Petrobras scraping error: {e}")
            return []
    
    def scrape_combustivel_api(self) -> List[Dict]:
        """Scrape from combustivelapi.com.br"""
        try:
            # This API might require authentication or have rate limits
            url = "https://combustivelapi.com.br/api/precos"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                prices = []
                for item in data.get('precos', []):
                    prices.append({
                        'source': 'combustivel_api',
                        'fuel_type': self.normalize_fuel_type(item.get('combustivel')),
                        'price': float(item.get('preco', 0)),
                        'location': item.get('cidade', ''),
                        'state': item.get('estado', ''),
                        'station_name': item.get('posto', ''),
                        'confidence': 0.8,
                        'scraped_at': datetime.now(timezone.utc)
                    })
                
                current_app.logger.info(f"Scraped {len(prices)} prices from Combustível API")
                return prices
            
        except Exception as e:
            current_app.logger.error(f"Combustível API scraping error: {e}")
        
        return []
    
    def scrape_local_gas_station_websites(self, station_urls: List[str]) -> List[Dict]:
        """Scrape prices from individual gas station websites"""
        prices = []
        
        for url in station_urls:
            try:
                time.sleep(random.uniform(1, 3))  # Rate limiting
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for price information
                price_elements = soup.find_all(text=re.compile(r'R\$\s*\d+[,\.]\d{2,3}'))
                
                for price_text in price_elements:
                    price_match = re.search(r'R\$\s*(\d+[,\.]\d{2,3})', price_text)
                    if price_match:
                        price_value = float(price_match.group(1).replace(',', '.'))
                        
                        # Try to determine fuel type from surrounding context
                        parent = price_text.parent if hasattr(price_text, 'parent') else None
                        context = parent.get_text() if parent else price_text
                        
                        fuel_type = self.detect_fuel_type(context)
                        
                        if fuel_type:
                            prices.append({
                                'source': f'website_{url}',
                                'fuel_type': fuel_type,
                                'price': price_value,
                                'url': url,
                                'confidence': 0.6,
                                'scraped_at': datetime.now(timezone.utc)
                            })
                
            except Exception as e:
                current_app.logger.error(f"Error scraping {url}: {e}")
                continue
        
        return prices
    
    def detect_fuel_type(self, text: str) -> Optional[str]:
        """Detect fuel type from text context"""
        text_lower = text.lower()
        
        # Fuel type patterns
        patterns = {
            'gasoline': ['gasolina', 'gasoline', 'gas comum', 'gas aditivada'],
            'ethanol': ['etanol', 'álcool', 'alcool', 'ethanol'],
            'diesel': ['diesel comum', 'diesel', 'óleo diesel'],
            'diesel_s10': ['diesel s10', 's10', 'diesel s-10'],
            'gnv': ['gnv', 'gás natural', 'gas natural']
        }
        
        for fuel_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return fuel_type
        
        return None
    
    def normalize_fuel_type(self, fuel_type: str) -> str:
        """Normalize fuel type to standard format"""
        if not fuel_type:
            return 'gasoline'
        
        fuel_lower = fuel_type.lower()
        
        if any(word in fuel_lower for word in ['gasolina', 'gasoline']):
            return 'gasoline'
        elif any(word in fuel_lower for word in ['etanol', 'álcool', 'alcool']):
            return 'ethanol'
        elif 's10' in fuel_lower or 's-10' in fuel_lower:
            return 'diesel_s10'
        elif 'diesel' in fuel_lower:
            return 'diesel'
        elif any(word in fuel_lower for word in ['gnv', 'gás natural']):
            return 'gnv'
        
        return 'gasoline'  # Default
    
    def update_database_prices(self, scraped_prices: List[Dict]) -> Dict:
        """Update database with scraped prices"""
        stats = {
            'processed': 0,
            'updated': 0,
            'created': 0,
            'errors': 0
        }
        
        for price_data in scraped_prices:
            try:
                stats['processed'] += 1
                
                # Find or create gas station
                station = None
                
                if price_data.get('station_name') and price_data.get('location'):
                    # Try to find existing station
                    station = GasStation.query.filter_by(
                        name=price_data['station_name']
                    ).first()
                    
                    if not station:
                        # Create new station with minimal data
                        station = GasStation(
                            name=price_data['station_name'],
                            address=price_data.get('location', ''),
                            city=price_data.get('location', '').split(',')[0] if ',' in price_data.get('location', '') else price_data.get('location', ''),
                            state=price_data.get('state', 'SP'),
                            latitude=-23.5505,  # Default São Paulo coordinates
                            longitude=-46.6333,
                            data_source='web_scraping',
                            data_confidence=price_data.get('confidence', 0.5)
                        )
                        db.session.add(station)
                        db.session.flush()  # Get ID
                        stats['created'] += 1
                
                if station:
                    # Check if price already exists (recent)
                    existing_price = FuelPrice.query.filter_by(
                        gas_station_id=station.id,
                        fuel_type=price_data['fuel_type']
                    ).filter(
                        FuelPrice.reported_at > datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
                    ).first()
                    
                    if existing_price:
                        # Update existing price
                        existing_price.price = price_data['price']
                        existing_price.source = price_data['source']
                        existing_price.source_confidence = price_data.get('confidence', 0.5)
                        existing_price.reported_at = price_data.get('scraped_at', datetime.now(timezone.utc))
                        stats['updated'] += 1
                    else:
                        # Create new price
                        new_price = FuelPrice(
                            gas_station_id=station.id,
                            fuel_type=price_data['fuel_type'],
                            price=price_data['price'],
                            source=price_data['source'],
                            source_confidence=price_data.get('confidence', 0.5),
                            reported_at=price_data.get('scraped_at', datetime.now(timezone.utc))
                        )
                        db.session.add(new_price)
                        stats['created'] += 1
                
            except Exception as e:
                current_app.logger.error(f"Error updating price data: {e}")
                stats['errors'] += 1
                continue
        
        try:
            db.session.commit()
            current_app.logger.info(f"Price update stats: {stats}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database commit error: {e}")
            stats['errors'] += stats['processed']
            stats['updated'] = 0
            stats['created'] = 0
        
        return stats
    
    def run_full_scraping_cycle(self) -> Dict:
        """Run complete scraping cycle from all sources"""
        current_app.logger.info("Starting full fuel price scraping cycle")
        
        all_prices = []
        
        # Scrape from different sources
        sources = [
            ('petrobras', self.scrape_petrobras_prices),
            ('combustivel_api', self.scrape_combustivel_api),
            ('anp', lambda: self.scrape_anp_prices('SP'))
        ]
        
        for source_name, scraper_func in sources:
            try:
                current_app.logger.info(f"Scraping from {source_name}")
                prices = scraper_func()
                all_prices.extend(prices)
                
                # Rate limiting between sources
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                current_app.logger.error(f"Error scraping {source_name}: {e}")
                continue
        
        # Update database
        stats = self.update_database_prices(all_prices)
        
        # Log scraping activity
        from src.models.gas_station import db
        try:
            # You would create a ScrapingLog model for this
            current_app.logger.info(f"Scraping completed: {stats}")
        except Exception as e:
            current_app.logger.error(f"Error logging scraping activity: {e}")
        
        return {
            'total_scraped': len(all_prices),
            'update_stats': stats,
            'sources_used': len(sources),
            'completed_at': datetime.now(timezone.utc).isoformat()
        }

# Global scraper instance
fuel_scraper = FuelPriceScraper()

