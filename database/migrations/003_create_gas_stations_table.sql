-- =====================================================
-- MIGRAÇÃO 003: CRIAR TABELA DE POSTOS DE COMBUSTÍVEL
-- =====================================================

-- Criar tabela de postos de combustível
CREATE TABLE IF NOT EXISTS gas_stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    phone VARCHAR(20),
    opening_hours TEXT,
    services TEXT[], -- Array de serviços (loja, banheiro, etc.)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_gas_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_gas_longitude CHECK (longitude BETWEEN -180 AND 180)
);

-- Criar tabela de preços de combustível
CREATE TABLE IF NOT EXISTS fuel_prices (
    id SERIAL PRIMARY KEY,
    gas_station_id INTEGER NOT NULL REFERENCES gas_stations(id) ON DELETE CASCADE,
    fuel_type VARCHAR(20) NOT NULL,
    price DECIMAL(6, 3) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'manual', -- manual, api, scraping
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT chk_fuel_price_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    CONSTRAINT chk_fuel_price_value CHECK (price > 0),
    
    -- Unique constraint para evitar duplicatas
    UNIQUE(gas_station_id, fuel_type)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_gas_stations_location ON gas_stations(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_gas_stations_brand ON gas_stations(brand);
CREATE INDEX IF NOT EXISTS idx_gas_stations_active ON gas_stations(is_active);
CREATE INDEX IF NOT EXISTS idx_gas_stations_name ON gas_stations(name);

CREATE INDEX IF NOT EXISTS idx_fuel_prices_station ON fuel_prices(gas_station_id);
CREATE INDEX IF NOT EXISTS idx_fuel_prices_type ON fuel_prices(fuel_type);
CREATE INDEX IF NOT EXISTS idx_fuel_prices_updated ON fuel_prices(last_updated);
CREATE INDEX IF NOT EXISTS idx_fuel_prices_active ON fuel_prices(is_active);
CREATE INDEX IF NOT EXISTS idx_fuel_prices_price ON fuel_prices(price);

-- Comentários para documentação
COMMENT ON TABLE gas_stations IS 'Postos de combustível cadastrados no sistema';
COMMENT ON COLUMN gas_stations.name IS 'Nome do posto de combustível';
COMMENT ON COLUMN gas_stations.brand IS 'Marca/bandeira do posto (Shell, Ipiranga, etc.)';
COMMENT ON COLUMN gas_stations.address IS 'Endereço completo do posto';
COMMENT ON COLUMN gas_stations.latitude IS 'Latitude da localização do posto';
COMMENT ON COLUMN gas_stations.longitude IS 'Longitude da localização do posto';
COMMENT ON COLUMN gas_stations.services IS 'Array de serviços disponíveis no posto';

COMMENT ON TABLE fuel_prices IS 'Preços de combustíveis por posto';
COMMENT ON COLUMN fuel_prices.gas_station_id IS 'Referência ao posto de combustível';
COMMENT ON COLUMN fuel_prices.fuel_type IS 'Tipo de combustível (gasoline, ethanol, diesel, diesel_s10, gnv)';
COMMENT ON COLUMN fuel_prices.price IS 'Preço por litro do combustível';
COMMENT ON COLUMN fuel_prices.source IS 'Fonte da informação do preço (manual, api, scraping)';

