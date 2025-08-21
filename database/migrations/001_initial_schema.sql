-- Migration: 001_initial_schema.sql
-- Description: Initial database schema for Tanque Cheio application
-- Created: 2025-08-21

-- Enable PostGIS extension for geospatial operations
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles with GPS preferences
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_fuel_type VARCHAR(20) NOT NULL DEFAULT 'gasoline' CHECK (preferred_fuel_type IN ('gasoline', 'ethanol', 'gnv', 'diesel', 'diesel_s10')),
    notification_enabled BOOLEAN DEFAULT TRUE,
    notification_interval_km INTEGER DEFAULT 100 CHECK (notification_interval_km > 0),
    notification_radius_km INTEGER DEFAULT 50 CHECK (notification_radius_km > 0),
    last_location GEOMETRY(POINT, 4326),
    last_location_update TIMESTAMP WITH TIME ZONE,
    total_distance_km DECIMAL(10,2) DEFAULT 0.0,
    last_notification_km DECIMAL(10,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gas stations
CREATE TABLE gas_stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    postal_code VARCHAR(10),
    location GEOMETRY(POINT, 4326) NOT NULL,
    phone VARCHAR(20),
    operating_hours JSONB,
    amenities JSONB,
    partner_id UUID,
    data_source VARCHAR(50) DEFAULT 'manual',
    data_confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (data_confidence >= 0 AND data_confidence <= 1),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fuel prices
CREATE TABLE fuel_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gas_station_id UUID NOT NULL REFERENCES gas_stations(id) ON DELETE CASCADE,
    fuel_type VARCHAR(20) NOT NULL CHECK (fuel_type IN ('gasoline', 'ethanol', 'gnv', 'diesel', 'diesel_s10')),
    price DECIMAL(6,3) NOT NULL CHECK (price > 0),
    source VARCHAR(50) NOT NULL,
    source_confidence DECIMAL(3,2) DEFAULT 0.5 CHECK (source_confidence >= 0 AND source_confidence <= 1),
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- GPS tracking history
CREATE TABLE gps_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    location GEOMETRY(POINT, 4326) NOT NULL,
    accuracy DECIMAL(8,2),
    speed DECIMAL(6,2),
    heading DECIMAL(5,2),
    trip_id UUID,
    distance_from_last DECIMAL(8,3) DEFAULT 0.0,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications sent to users
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'fuel_recommendation',
    gas_station_id UUID REFERENCES gas_stations(id),
    fuel_price_id UUID REFERENCES fuel_prices(id),
    user_location GEOMETRY(POINT, 4326),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    delivery_status VARCHAR(20) DEFAULT 'sent'
);

-- Coupons and vouchers
CREATE TABLE coupons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gas_station_id UUID NOT NULL REFERENCES gas_stations(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed_amount')),
    discount_value DECIMAL(6,2) NOT NULL CHECK (discount_value > 0),
    fuel_types JSONB,
    min_liters DECIMAL(6,2),
    min_amount DECIMAL(8,2),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Routes calculated for users
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    origin_location GEOMETRY(POINT, 4326) NOT NULL,
    destination_location GEOMETRY(POINT, 4326) NOT NULL,
    origin_address TEXT,
    destination_address TEXT,
    distance_km DECIMAL(8,2) NOT NULL,
    estimated_duration_minutes INTEGER,
    estimated_fuel_needed DECIMAL(6,2),
    route_geometry GEOMETRY(LINESTRING, 4326),
    preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Route recommendations (gas stations along routes)
CREATE TABLE route_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    gas_station_id UUID NOT NULL REFERENCES gas_stations(id) ON DELETE CASCADE,
    fuel_price_id UUID NOT NULL REFERENCES fuel_prices(id) ON DELETE CASCADE,
    detour_distance_km DECIMAL(6,2) NOT NULL,
    detour_time_minutes INTEGER,
    savings_amount DECIMAL(6,2),
    recommendation_score DECIMAL(4,2),
    position_on_route DECIMAL(4,2), -- 0.0 to 1.0, where 0 is start and 1 is end
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Partner accounts for gas stations
CREATE TABLE partners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    api_key VARCHAR(255) UNIQUE NOT NULL,
    api_key_expires TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit_per_hour INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price validation reports from crowdsourcing
CREATE TABLE price_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fuel_price_id UUID NOT NULL REFERENCES fuel_prices(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reported_price DECIMAL(6,3) NOT NULL,
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('confirm', 'dispute', 'update')),
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 5),
    photo_url VARCHAR(500),
    notes TEXT,
    location GEOMETRY(POINT, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data scraping logs
CREATE TABLE scraping_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL,
    scraping_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    records_success INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE,
    execution_time_seconds INTEGER
);

-- User sessions for JWT token management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_fuel_type ON user_profiles(preferred_fuel_type);

-- Spatial indexes
CREATE INDEX idx_gas_stations_location ON gas_stations USING GIST(location);
CREATE INDEX idx_gps_tracking_location ON gps_tracking USING GIST(location);
CREATE INDEX idx_notifications_user_location ON notifications USING GIST(user_location);

-- Regular indexes
CREATE INDEX idx_gas_stations_brand ON gas_stations(brand);
CREATE INDEX idx_gas_stations_city ON gas_stations(city, state);
CREATE INDEX idx_gas_stations_active ON gas_stations(is_active);

CREATE INDEX idx_fuel_prices_station_fuel ON fuel_prices(gas_station_id, fuel_type);
CREATE INDEX idx_fuel_prices_active ON fuel_prices(is_active);
CREATE INDEX idx_fuel_prices_reported_at ON fuel_prices(reported_at DESC);

CREATE INDEX idx_gps_tracking_user_trip ON gps_tracking(user_profile_id, trip_id);
CREATE INDEX idx_gps_tracking_recorded_at ON gps_tracking(recorded_at DESC);

CREATE INDEX idx_notifications_user_sent ON notifications(user_profile_id, sent_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_profile_id) WHERE read_at IS NULL;

CREATE INDEX idx_coupons_station_active ON coupons(gas_station_id) WHERE is_active = TRUE;
CREATE INDEX idx_coupons_valid_period ON coupons(valid_from, valid_until) WHERE is_active = TRUE;

CREATE INDEX idx_routes_user_created ON routes(user_profile_id, created_at DESC);
CREATE INDEX idx_route_recommendations_route ON route_recommendations(route_id);

CREATE INDEX idx_partners_api_key ON partners(api_key);
CREATE INDEX idx_partners_active ON partners(is_active);

CREATE INDEX idx_price_reports_fuel_price ON price_reports(fuel_price_id);
CREATE INDEX idx_price_reports_created ON price_reports(created_at DESC);

CREATE INDEX idx_user_sessions_user_active ON user_sessions(user_id) WHERE is_active = TRUE;
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gas_stations_updated_at BEFORE UPDATE ON gas_stations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fuel_prices_updated_at BEFORE UPDATE ON fuel_prices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_partners_updated_at BEFORE UPDATE ON partners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW active_fuel_prices AS
SELECT 
    fp.*,
    gs.name as station_name,
    gs.brand,
    gs.location,
    gs.city,
    gs.state
FROM fuel_prices fp
JOIN gas_stations gs ON fp.gas_station_id = gs.id
WHERE fp.is_active = TRUE 
  AND gs.is_active = TRUE
  AND fp.reported_at > NOW() - INTERVAL '7 days';

CREATE VIEW user_notification_stats AS
SELECT 
    up.id as user_profile_id,
    up.user_id,
    COUNT(n.id) as total_notifications,
    COUNT(CASE WHEN n.read_at IS NOT NULL THEN 1 END) as read_notifications,
    COUNT(CASE WHEN n.clicked_at IS NOT NULL THEN 1 END) as clicked_notifications,
    MAX(n.sent_at) as last_notification_sent
FROM user_profiles up
LEFT JOIN notifications n ON up.id = n.user_profile_id
GROUP BY up.id, up.user_id;

-- Insert default data
INSERT INTO users (id, email, password_hash, name, email_verified) VALUES
('00000000-0000-0000-0000-000000000001', 'admin@tanquecheio.app', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/VcSAg/9qK', 'Admin System', TRUE);

-- Migration completed
INSERT INTO scraping_logs (source_name, scraping_type, status, records_processed, records_success) 
VALUES ('migration', 'initial_schema', 'completed', 1, 1);

