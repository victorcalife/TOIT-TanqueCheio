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

-- Comentários para documentação
COMMENT ON TABLE trips IS 'Viagens realizadas pelos usuários';
COMMENT ON COLUMN trips.user_id IS 'Referência ao usuário que fez a viagem';
COMMENT ON COLUMN trips.origin IS 'Local de origem da viagem';
COMMENT ON COLUMN trips.destination IS 'Local de destino da viagem';
COMMENT ON COLUMN trips.fuel_type IS 'Tipo de combustível usado na viagem';
COMMENT ON COLUMN trips.total_distance_km IS 'Distância total percorrida em km';
COMMENT ON COLUMN trips.estimated_fuel_consumption IS 'Consumo estimado de combustível';
COMMENT ON COLUMN trips.actual_fuel_consumption IS 'Consumo real de combustível';
COMMENT ON COLUMN trips.total_savings IS 'Economia total obtida na viagem';
COMMENT ON COLUMN trips.is_active IS 'Se a viagem está ativa (em andamento)';

COMMENT ON TABLE gps_tracking IS 'Pontos de rastreamento GPS dos usuários';
COMMENT ON COLUMN gps_tracking.user_id IS 'Referência ao usuário';
COMMENT ON COLUMN gps_tracking.trip_id IS 'Referência à viagem (opcional)';
COMMENT ON COLUMN gps_tracking.latitude IS 'Latitude do ponto GPS';
COMMENT ON COLUMN gps_tracking.longitude IS 'Longitude do ponto GPS';
COMMENT ON COLUMN gps_tracking.accuracy IS 'Precisão do GPS em metros';
COMMENT ON COLUMN gps_tracking.speed IS 'Velocidade no momento da captura';
COMMENT ON COLUMN gps_tracking.altitude IS 'Altitude em metros';
COMMENT ON COLUMN gps_tracking.heading IS 'Direção/rumo em graus';

