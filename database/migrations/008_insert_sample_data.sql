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

-- Inserir parceiro de exemplo
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

-- Inserir histórico de preços para IA (últimos 7 dias)
INSERT INTO price_history (gas_station_id, fuel_type, price, recorded_at)
SELECT gs.id, 'gasoline', 
    CASE 
        WHEN gs.name = 'Shell BR-101' THEN 5.82 + (random() - 0.5) * 0.10
        WHEN gs.name = 'Ipiranga Centro' THEN 5.67 + (random() - 0.5) * 0.08
        WHEN gs.name = 'Petrobras Rodovia' THEN 5.73 + (random() - 0.5) * 0.09
        WHEN gs.name = 'Posto Ale' THEN 5.75 + (random() - 0.5) * 0.07
        WHEN gs.name = 'BR Mania' THEN 5.79 + (random() - 0.5) * 0.06
    END,
    CURRENT_TIMESTAMP - (generate_series(0, 6) || ' days')::INTERVAL
FROM gas_stations gs
WHERE gs.is_active = true
ON CONFLICT DO NOTHING;

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

-- Inserir previsões de preços para os próximos 7 dias
INSERT INTO price_predictions (gas_station_id, fuel_type, current_price, predicted_price, prediction_date, confidence_level, trend_analysis)
SELECT gs.id, 'gasoline', fp.price,
    fp.price + (random() - 0.5) * 0.15, -- Variação de ±15 centavos
    CURRENT_DATE + (generate_series(1, 7) || ' days')::INTERVAL,
    85 - (generate_series(1, 7) * 3), -- Confiança decrescente
    CASE 
        WHEN random() < 0.4 THEN 'rising'
        WHEN random() < 0.8 THEN 'falling'
        ELSE 'stable'
    END
FROM gas_stations gs
JOIN fuel_prices fp ON gs.id = fp.gas_station_id
WHERE gs.is_active = true AND fp.fuel_type = 'gasoline'
ON CONFLICT DO NOTHING;

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

-- Comentários finais
COMMENT ON FUNCTION update_updated_at_column() IS 'Função para atualizar automaticamente o campo updated_at';

-- Verificar dados inseridos
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Gas Stations', COUNT(*) FROM gas_stations
UNION ALL
SELECT 'Fuel Prices', COUNT(*) FROM fuel_prices
UNION ALL
SELECT 'Partners', COUNT(*) FROM partners
UNION ALL
SELECT 'Coupons', COUNT(*) FROM coupons
UNION ALL
SELECT 'Price History', COUNT(*) FROM price_history
UNION ALL
SELECT 'Market Analysis', COUNT(*) FROM market_analysis
UNION ALL
SELECT 'Price Predictions', COUNT(*) FROM price_predictions;

