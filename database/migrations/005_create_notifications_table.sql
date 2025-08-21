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

-- Comentários para documentação
COMMENT ON TABLE notifications IS 'Notificações enviadas aos usuários';
COMMENT ON COLUMN notifications.user_id IS 'Referência ao usuário que recebeu a notificação';
COMMENT ON COLUMN notifications.trip_id IS 'Referência à viagem relacionada (opcional)';
COMMENT ON COLUMN notifications.gas_station_id IS 'Referência ao posto recomendado (opcional)';
COMMENT ON COLUMN notifications.type IS 'Tipo da notificação (fuel_recommendation, price_alert, etc.)';
COMMENT ON COLUMN notifications.title IS 'Título da notificação';
COMMENT ON COLUMN notifications.message IS 'Mensagem completa da notificação';
COMMENT ON COLUMN notifications.fuel_type IS 'Tipo de combustível relacionado';
COMMENT ON COLUMN notifications.recommended_price IS 'Preço recomendado do combustível';
COMMENT ON COLUMN notifications.estimated_savings IS 'Economia estimada';
COMMENT ON COLUMN notifications.distance_to_station IS 'Distância até o posto em km';
COMMENT ON COLUMN notifications.is_read IS 'Se a notificação foi lida';
COMMENT ON COLUMN notifications.is_clicked IS 'Se a notificação foi clicada';
COMMENT ON COLUMN notifications.expires_at IS 'Data de expiração da notificação';

