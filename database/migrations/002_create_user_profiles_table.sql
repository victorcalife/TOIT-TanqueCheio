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

-- Comentários para documentação
COMMENT ON TABLE user_profiles IS 'Perfis e configurações dos usuários';
COMMENT ON COLUMN user_profiles.user_id IS 'Referência ao usuário';
COMMENT ON COLUMN user_profiles.preferred_fuel_type IS 'Tipo de combustível preferido (gasoline, ethanol, diesel, diesel_s10, gnv)';
COMMENT ON COLUMN user_profiles.notification_interval_km IS 'Intervalo em km para notificações automáticas';
COMMENT ON COLUMN user_profiles.notifications_enabled IS 'Se as notificações estão habilitadas';
COMMENT ON COLUMN user_profiles.current_latitude IS 'Latitude atual do usuário';
COMMENT ON COLUMN user_profiles.current_longitude IS 'Longitude atual do usuário';
COMMENT ON COLUMN user_profiles.total_distance_traveled IS 'Distância total percorrida pelo usuário';
COMMENT ON COLUMN user_profiles.last_notification_km IS 'Quilometragem da última notificação enviada';

