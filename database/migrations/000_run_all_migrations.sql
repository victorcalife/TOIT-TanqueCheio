-- =====================================================
-- SCRIPT MASTER: EXECUTAR TODAS AS MIGRAÇÕES
-- =====================================================
-- Execute este arquivo no TablePlus para criar todo o banco
-- Ordem de execução das migrações do Tanque Cheio
-- =====================================================

-- Verificar versão do PostgreSQL
SELECT version();

-- Criar extensões necessárias (se disponíveis)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- Para UUIDs (opcional)
-- CREATE EXTENSION IF NOT EXISTS "postgis"; -- Para geolocalização avançada (opcional)

-- =====================================================
-- MIGRAÇÃO 001: CRIAR TABELA DE USUÁRIOS
-- =====================================================

-- Criar tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- =====================================================
-- MIGRAÇÃO 002: CRIAR TABELA DE PERFIS DE USUÁRIO
-- =====================================================

-- Criar tabela de perfis de usuário
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_fuel_type VARCHAR(20) DEFAULT 'gasoline',
    notification_interval_km INTEGER DEFAULT 100,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    current_latitude DECIMAL(10, 8),
    current_longitude DECIMAL(11, 8),
    total_distance_traveled DECIMAL(10, 2) DEFAULT 0.0,
    last_notification_km DECIMAL(10, 2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_fuel_type CHECK (preferred_fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    CONSTRAINT chk_interval_km CHECK (notification_interval_km > 0),
    CONSTRAINT chk_latitude CHECK (current_latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_longitude CHECK (current_longitude BETWEEN -180 AND 180),
    CONSTRAINT chk_distance CHECK (total_distance_traveled >= 0)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_fuel_type ON user_profiles(preferred_fuel_type);
CREATE INDEX IF NOT EXISTS idx_user_profiles_notifications ON user_profiles(notifications_enabled);
CREATE INDEX IF NOT EXISTS idx_user_profiles_location ON user_profiles(current_latitude, current_longitude);

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

-- =====================================================
-- MIGRAÇÃO 004: CRIAR TABELAS DE VIAGENS E GPS
-- =====================================================

-- Criar tabela de viagens
CREATE TABLE IF NOT EXISTS trips (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    origin VARCHAR(255),
    destination VARCHAR(255),
    fuel_type VARCHAR(20) DEFAULT 'gasoline',
    start_latitude DECIMAL(10, 8),
    start_longitude DECIMAL(11, 8),
    end_latitude DECIMAL(10, 8),
    end_longitude DECIMAL(11, 8),
    total_distance_km DECIMAL(10, 2) DEFAULT 0.0,
    estimated_fuel_consumption DECIMAL(8, 2),
    actual_fuel_consumption DECIMAL(8, 2),
    total_savings DECIMAL(8, 2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_trip_fuel_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    CONSTRAINT chk_trip_start_lat CHECK (start_latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_trip_start_lon CHECK (start_longitude BETWEEN -180 AND 180),
    CONSTRAINT chk_trip_end_lat CHECK (end_latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_trip_end_lon CHECK (end_longitude BETWEEN -180 AND 180),
    CONSTRAINT chk_trip_distance CHECK (total_distance_km >= 0),
    CONSTRAINT chk_trip_consumption CHECK (estimated_fuel_consumption >= 0),
    CONSTRAINT chk_trip_actual_consumption CHECK (actual_fuel_consumption >= 0)
);

-- Criar tabela de rastreamento GPS
CREATE TABLE IF NOT EXISTS gps_tracking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trip_id INTEGER REFERENCES trips(id) ON DELETE CASCADE,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    accuracy DECIMAL(6, 2) DEFAULT 10.0, -- Precisão em metros
    speed DECIMAL(6, 2) DEFAULT 0.0, -- Velocidade em km/h
    altitude DECIMAL(8, 2), -- Altitude em metros
    heading DECIMAL(5, 2), -- Direção em graus (0-360)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_gps_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_gps_longitude CHECK (longitude BETWEEN -180 AND 180),
    CONSTRAINT chk_gps_accuracy CHECK (accuracy >= 0),
    CONSTRAINT chk_gps_speed CHECK (speed >= 0),
    CONSTRAINT chk_gps_heading CHECK (heading BETWEEN 0 AND 360)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_active ON trips(is_active);
CREATE INDEX IF NOT EXISTS idx_trips_started_at ON trips(started_at);
CREATE INDEX IF NOT EXISTS idx_trips_fuel_type ON trips(fuel_type);

CREATE INDEX IF NOT EXISTS idx_gps_user_id ON gps_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_gps_trip_id ON gps_tracking(trip_id);
CREATE INDEX IF NOT EXISTS idx_gps_timestamp ON gps_tracking(timestamp);
CREATE INDEX IF NOT EXISTS idx_gps_location ON gps_tracking(latitude, longitude);

-- =====================================================
-- MIGRAÇÃO 005: CRIAR TABELA DE NOTIFICAÇÕES
-- =====================================================

-- Criar tabela de notificações
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trip_id INTEGER REFERENCES trips(id) ON DELETE SET NULL,
    gas_station_id INTEGER REFERENCES gas_stations(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'fuel_recommendation',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    fuel_type VARCHAR(20),
    recommended_price DECIMAL(6, 3),
    estimated_savings DECIMAL(8, 2),
    distance_to_station DECIMAL(6, 2),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_read BOOLEAN DEFAULT FALSE,
    is_clicked BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    clicked_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_notif_type CHECK (type IN ('fuel_recommendation', 'price_alert', 'trip_start', 'trip_end', 'system')),
    CONSTRAINT chk_notif_fuel_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv') OR fuel_type IS NULL),
    CONSTRAINT chk_notif_price CHECK (recommended_price > 0 OR recommended_price IS NULL),
    CONSTRAINT chk_notif_savings CHECK (estimated_savings >= 0 OR estimated_savings IS NULL),
    CONSTRAINT chk_notif_distance CHECK (distance_to_station >= 0 OR distance_to_station IS NULL),
    CONSTRAINT chk_notif_latitude CHECK (latitude BETWEEN -90 AND 90 OR latitude IS NULL),
    CONSTRAINT chk_notif_longitude CHECK (longitude BETWEEN -180 AND 180 OR longitude IS NULL)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_trip_id ON notifications(trip_id);
CREATE INDEX IF NOT EXISTS idx_notifications_station_id ON notifications(gas_station_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);
CREATE INDEX IF NOT EXISTS idx_notifications_expires_at ON notifications(expires_at);
CREATE INDEX IF NOT EXISTS idx_notifications_fuel_type ON notifications(fuel_type);

-- =====================================================
-- MIGRAÇÃO 006: CRIAR TABELAS DE PARCEIROS E CUPONS
-- =====================================================

-- Criar tabela de parceiros
CREATE TABLE IF NOT EXISTS partners (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    website VARCHAR(255),
    commission_rate DECIMAL(5, 4) DEFAULT 0.0000, -- Taxa de comissão (ex: 0.0500 = 5%)
    contract_start_date DATE,
    contract_end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_partner_commission CHECK (commission_rate >= 0 AND commission_rate <= 1)
);

-- Criar tabela de cupons/vouchers
CREATE TABLE IF NOT EXISTS coupons (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER REFERENCES partners(id) ON DELETE SET NULL,
    gas_station_id INTEGER REFERENCES gas_stations(id) ON DELETE SET NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20) NOT NULL DEFAULT 'percentage',
    discount_value DECIMAL(8, 2) NOT NULL,
    fuel_type VARCHAR(20),
    min_liters DECIMAL(6, 2),
    min_purchase_amount DECIMAL(8, 2),
    max_discount_amount DECIMAL(8, 2),
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_coupon_discount_type CHECK (discount_type IN ('percentage', 'fixed', 'per_liter')),
    CONSTRAINT chk_coupon_discount_value CHECK (discount_value > 0),
    CONSTRAINT chk_coupon_fuel_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv', 'any') OR fuel_type IS NULL),
    CONSTRAINT chk_coupon_min_liters CHECK (min_liters > 0 OR min_liters IS NULL),
    CONSTRAINT chk_coupon_min_purchase CHECK (min_purchase_amount > 0 OR min_purchase_amount IS NULL),
    CONSTRAINT chk_coupon_max_discount CHECK (max_discount_amount > 0 OR max_discount_amount IS NULL),
    CONSTRAINT chk_coupon_usage_limit CHECK (usage_limit > 0 OR usage_limit IS NULL),
    CONSTRAINT chk_coupon_usage_count CHECK (usage_count >= 0)
);

-- Criar tabela de uso de cupons
CREATE TABLE IF NOT EXISTS coupon_usage (
    id SERIAL PRIMARY KEY,
    coupon_id INTEGER NOT NULL REFERENCES coupons(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trip_id INTEGER REFERENCES trips(id) ON DELETE SET NULL,
    gas_station_id INTEGER REFERENCES gas_stations(id) ON DELETE SET NULL,
    fuel_type VARCHAR(20),
    liters_purchased DECIMAL(6, 2),
    original_price DECIMAL(6, 3),
    discount_applied DECIMAL(8, 2),
    final_price DECIMAL(8, 2),
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_usage_fuel_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    CONSTRAINT chk_usage_liters CHECK (liters_purchased > 0 OR liters_purchased IS NULL),
    CONSTRAINT chk_usage_original_price CHECK (original_price > 0 OR original_price IS NULL),
    CONSTRAINT chk_usage_discount CHECK (discount_applied >= 0 OR discount_applied IS NULL),
    CONSTRAINT chk_usage_final_price CHECK (final_price >= 0 OR final_price IS NULL)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_partners_active ON partners(is_active);
CREATE INDEX IF NOT EXISTS idx_partners_brand ON partners(brand);
CREATE INDEX IF NOT EXISTS idx_partners_commission ON partners(commission_rate);

CREATE INDEX IF NOT EXISTS idx_coupons_partner_id ON coupons(partner_id);
CREATE INDEX IF NOT EXISTS idx_coupons_station_id ON coupons(gas_station_id);
CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code);
CREATE INDEX IF NOT EXISTS idx_coupons_active ON coupons(is_active);
CREATE INDEX IF NOT EXISTS idx_coupons_fuel_type ON coupons(fuel_type);
CREATE INDEX IF NOT EXISTS idx_coupons_valid_until ON coupons(valid_until);
CREATE INDEX IF NOT EXISTS idx_coupons_discount_type ON coupons(discount_type);

CREATE INDEX IF NOT EXISTS idx_coupon_usage_coupon_id ON coupon_usage(coupon_id);
CREATE INDEX IF NOT EXISTS idx_coupon_usage_user_id ON coupon_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_coupon_usage_trip_id ON coupon_usage(trip_id);
CREATE INDEX IF NOT EXISTS idx_coupon_usage_station_id ON coupon_usage(gas_station_id);
CREATE INDEX IF NOT EXISTS idx_coupon_usage_used_at ON coupon_usage(used_at);

-- =====================================================
-- MIGRAÇÃO 007: CRIAR TABELA DE HISTÓRICO DE PREÇOS
-- =====================================================

-- Criar tabela de histórico de preços para IA
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    gas_station_id INTEGER NOT NULL REFERENCES gas_stations(id) ON DELETE CASCADE,
    fuel_type VARCHAR(20) NOT NULL,
    price DECIMAL(6, 3) NOT NULL,
    previous_price DECIMAL(6, 3),
    price_change DECIMAL(6, 3), -- Diferença em relação ao preço anterior
    price_change_percent DECIMAL(5, 2), -- Percentual de mudança
    source VARCHAR(50) DEFAULT 'manual',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_price_hist_fuel_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    CONSTRAINT chk_price_hist_price CHECK (price > 0),
    CONSTRAINT chk_price_hist_prev_price CHECK (previous_price > 0 OR previous_price IS NULL)
);

-- Criar tabela de análises de mercado (para IA)
CREATE TABLE IF NOT EXISTS market_analysis (
    id SERIAL PRIMARY KEY,
    fuel_type VARCHAR(20) NOT NULL,
    region VARCHAR(100) DEFAULT 'sul_brasil',
    average_price DECIMAL(6, 3) NOT NULL,
    min_price DECIMAL(6, 3) NOT NULL,
    max_price DECIMAL(6, 3) NOT NULL,
    median_price DECIMAL(6, 3),
    std_deviation DECIMAL(6, 3),
    volatility_level VARCHAR(20), -- low, medium, high
    trend_direction VARCHAR(20), -- rising, falling, stable
    trend_strength DECIMAL(5, 2), -- Força da tendência (0-100)
    sample_size INTEGER DEFAULT 0,
    analysis_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_market_fuel_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    CONSTRAINT chk_market_avg_price CHECK (average_price > 0),
    CONSTRAINT chk_market_min_price CHECK (min_price > 0),
    CONSTRAINT chk_market_max_price CHECK (max_price > 0),
    CONSTRAINT chk_market_volatility CHECK (volatility_level IN ('low', 'medium', 'high') OR volatility_level IS NULL),
    CONSTRAINT chk_market_trend CHECK (trend_direction IN ('rising', 'falling', 'stable') OR trend_direction IS NULL),
    CONSTRAINT chk_market_strength CHECK (trend_strength BETWEEN 0 AND 100 OR trend_strength IS NULL),
    CONSTRAINT chk_market_sample CHECK (sample_size >= 0),
    
    -- Unique constraint para evitar duplicatas por dia
    UNIQUE(fuel_type, region, analysis_date)
);

-- Criar tabela de previsões de preços (IA)
CREATE TABLE IF NOT EXISTS price_predictions (
    id SERIAL PRIMARY KEY,
    gas_station_id INTEGER REFERENCES gas_stations(id) ON DELETE CASCADE,
    fuel_type VARCHAR(20) NOT NULL,
    current_price DECIMAL(6, 3) NOT NULL,
    predicted_price DECIMAL(6, 3) NOT NULL,
    prediction_date DATE NOT NULL,
    confidence_level DECIMAL(5, 2), -- 0-100%
    trend_analysis VARCHAR(20), -- rising, falling, stable
    algorithm_used VARCHAR(50) DEFAULT 'linear_regression',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_pred_fuel_type CHECK (fuel_type IN ('gasoline', 'ethanol', 'diesel', 'diesel_s10', 'gnv')),
    CONSTRAINT chk_pred_current_price CHECK (current_price > 0),
    CONSTRAINT chk_pred_predicted_price CHECK (predicted_price > 0),
    CONSTRAINT chk_pred_confidence CHECK (confidence_level BETWEEN 0 AND 100 OR confidence_level IS NULL),
    CONSTRAINT chk_pred_trend CHECK (trend_analysis IN ('rising', 'falling', 'stable') OR trend_analysis IS NULL)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_price_history_station_fuel ON price_history(gas_station_id, fuel_type);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded_at ON price_history(recorded_at);
CREATE INDEX IF NOT EXISTS idx_price_history_fuel_type ON price_history(fuel_type);
CREATE INDEX IF NOT EXISTS idx_price_history_price ON price_history(price);

CREATE INDEX IF NOT EXISTS idx_market_analysis_fuel_region ON market_analysis(fuel_type, region);
CREATE INDEX IF NOT EXISTS idx_market_analysis_date ON market_analysis(analysis_date);
CREATE INDEX IF NOT EXISTS idx_market_analysis_trend ON market_analysis(trend_direction);
CREATE INDEX IF NOT EXISTS idx_market_analysis_volatility ON market_analysis(volatility_level);

CREATE INDEX IF NOT EXISTS idx_price_predictions_station_fuel ON price_predictions(gas_station_id, fuel_type);
CREATE INDEX IF NOT EXISTS idx_price_predictions_date ON price_predictions(prediction_date);
CREATE INDEX IF NOT EXISTS idx_price_predictions_confidence ON price_predictions(confidence_level);
CREATE INDEX IF NOT EXISTS idx_price_predictions_trend ON price_predictions(trend_analysis);

-- =====================================================
-- MIGRAÇÃO 008: INSERIR DADOS DE EXEMPLO
-- =====================================================

-- Inserir usuário de exemplo
INSERT INTO users (name, email, phone, password_hash) VALUES 
('João Motorista GPS', 'joao.motorista@gmail.com', '+55 47 99999-8888', 'scrypt:32768:8:1$KQJxGzBqLKOQJxGz$b1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef')
ON CONFLICT (email) DO NOTHING;

-- Inserir perfil do usuário
INSERT INTO user_profiles (user_id, preferred_fuel_type, notification_interval_km, notifications_enabled, current_latitude, current_longitude, total_distance_traveled)
SELECT u.id, 'gasoline', 100, true, -26.9194, -49.0661, 0.0
FROM users u WHERE u.email = 'joao.motorista@gmail.com'
ON CONFLICT DO NOTHING;

-- Inserir postos de combustível
INSERT INTO gas_stations (name, brand, address, latitude, longitude, phone, is_active) VALUES 
('Shell BR-101', 'Shell', 'BR-101, Km 142, Balneário Camboriú - SC', -26.9194, -49.0661, '+55 47 3367-1234', true),
('Ipiranga Centro', 'Ipiranga', 'Av. Brasil, 1500, Centro, Balneário Camboriú - SC', -26.9766, -48.6354, '+55 47 3367-5678', true),
('Petrobras Rodovia', 'Petrobras', 'BR-470, Km 89, Navegantes - SC', -26.8986, -48.6516, '+55 47 3349-9012', true),
('Posto Ale', 'Ale', 'Rua 1500, 789, Balneário Camboriú - SC', -26.9850, -48.6200, '+55 47 3367-3456', true),
('BR Mania', 'BR', 'Av. Atlântica, 2000, Balneário Camboriú - SC', -26.9900, -48.6100, '+55 47 3367-7890', true)
ON CONFLICT DO NOTHING;

-- Inserir preços de combustível
INSERT INTO fuel_prices (gas_station_id, fuel_type, price, last_updated) 
SELECT gs.id, 'gasoline', 5.82, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Shell BR-101'
UNION ALL
SELECT gs.id, 'ethanol', 4.15, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Shell BR-101'
UNION ALL
SELECT gs.id, 'diesel', 5.95, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Shell BR-101'
UNION ALL
SELECT gs.id, 'gasoline', 5.67, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Ipiranga Centro'
UNION ALL
SELECT gs.id, 'ethanol', 4.02, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Ipiranga Centro'
UNION ALL
SELECT gs.id, 'diesel', 5.78, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Ipiranga Centro'
UNION ALL
SELECT gs.id, 'diesel_s10', 5.89, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Ipiranga Centro'
UNION ALL
SELECT gs.id, 'gasoline', 5.73, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Petrobras Rodovia'
UNION ALL
SELECT gs.id, 'ethanol', 4.08, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Petrobras Rodovia'
UNION ALL
SELECT gs.id, 'diesel', 5.84, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Petrobras Rodovia'
UNION ALL
SELECT gs.id, 'gnv', 3.45, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Petrobras Rodovia'
UNION ALL
SELECT gs.id, 'gasoline', 5.75, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Posto Ale'
UNION ALL
SELECT gs.id, 'ethanol', 4.10, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'Posto Ale'
UNION ALL
SELECT gs.id, 'gasoline', 5.79, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'BR Mania'
UNION ALL
SELECT gs.id, 'diesel', 5.87, CURRENT_TIMESTAMP FROM gas_stations gs WHERE gs.name = 'BR Mania'
ON CONFLICT (gas_station_id, fuel_type) DO UPDATE SET 
    price = EXCLUDED.price,
    last_updated = EXCLUDED.last_updated;

-- Inserir parceiros de exemplo
INSERT INTO partners (name, brand, contact_email, contact_phone, commission_rate, is_active) VALUES 
('Rede Shell Brasil', 'Shell', 'parceria@shell.com.br', '+55 11 3000-0000', 0.0500, true),
('Ipiranga Distribuidora', 'Ipiranga', 'parceiros@ipiranga.com.br', '+55 11 2000-0000', 0.0450, true)
ON CONFLICT DO NOTHING;

-- Inserir cupons de exemplo
INSERT INTO coupons (partner_id, code, title, description, discount_type, discount_value, fuel_type, valid_until, is_active)
SELECT p.id, 'SHELL10', 'Desconto Shell 10%', 'Desconto de 10% na gasolina Shell', 'percentage', 10.0, 'gasoline', CURRENT_TIMESTAMP + INTERVAL '30 days', true
FROM partners p WHERE p.name = 'Rede Shell Brasil'
UNION ALL
SELECT p.id, 'IPIRANGA5', 'R$ 5 OFF Ipiranga', 'R$ 5,00 de desconto no Ipiranga', 'fixed', 5.0, 'any', CURRENT_TIMESTAMP + INTERVAL '15 days', true
FROM partners p WHERE p.name = 'Ipiranga Distribuidora'
ON CONFLICT (code) DO NOTHING;

-- Inserir análise de mercado atual
INSERT INTO market_analysis (fuel_type, region, average_price, min_price, max_price, median_price, volatility_level, trend_direction, sample_size)
VALUES 
('gasoline', 'sul_brasil', 5.74, 5.67, 5.82, 5.73, 'medium', 'falling', 5),
('ethanol', 'sul_brasil', 4.09, 4.02, 4.15, 4.08, 'low', 'stable', 4),
('diesel', 'sul_brasil', 5.86, 5.78, 5.95, 5.84, 'medium', 'rising', 4),
('diesel_s10', 'sul_brasil', 5.89, 5.89, 5.89, 5.89, 'low', 'stable', 1),
('gnv', 'sul_brasil', 3.45, 3.45, 3.45, 3.45, 'low', 'stable', 1)
ON CONFLICT (fuel_type, region, analysis_date) DO UPDATE SET
    average_price = EXCLUDED.average_price,
    min_price = EXCLUDED.min_price,
    max_price = EXCLUDED.max_price,
    median_price = EXCLUDED.median_price,
    volatility_level = EXCLUDED.volatility_level,
    trend_direction = EXCLUDED.trend_direction,
    sample_size = EXCLUDED.sample_size;

-- =====================================================
-- FUNÇÕES E TRIGGERS
-- =====================================================

-- Criar função para atualizar timestamp de updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Criar triggers para atualizar updated_at automaticamente
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gas_stations_updated_at BEFORE UPDATE ON gas_stations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_partners_updated_at BEFORE UPDATE ON partners 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VERIFICAÇÃO FINAL
-- =====================================================

-- Verificar dados inseridos
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'User Profiles', COUNT(*) FROM user_profiles
UNION ALL
SELECT 'Gas Stations', COUNT(*) FROM gas_stations
UNION ALL
SELECT 'Fuel Prices', COUNT(*) FROM fuel_prices
UNION ALL
SELECT 'Partners', COUNT(*) FROM partners
UNION ALL
SELECT 'Coupons', COUNT(*) FROM coupons
UNION ALL
SELECT 'Market Analysis', COUNT(*) FROM market_analysis
ORDER BY table_name;

-- Verificar estrutura das tabelas principais
SELECT 
    schemaname,
    tablename,
    attname as column_name,
    typname as data_type
FROM pg_attribute 
JOIN pg_class ON pg_attribute.attrelid = pg_class.oid 
JOIN pg_type ON pg_attribute.atttypid = pg_type.oid 
JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid 
WHERE pg_namespace.nspname = 'public' 
    AND pg_class.relname IN ('users', 'gas_stations', 'fuel_prices', 'trips', 'notifications')
    AND pg_attribute.attnum > 0
ORDER BY tablename, attname;

-- =====================================================
-- MIGRAÇÃO CONCLUÍDA COM SUCESSO!
-- =====================================================
-- Todas as tabelas foram criadas com:
-- ✅ Constraints de integridade
-- ✅ Índices para performance
-- ✅ Dados de exemplo
-- ✅ Triggers automáticos
-- ✅ Comentários de documentação
-- 
-- O banco está pronto para o sistema Tanque Cheio IA!
-- =====================================================

