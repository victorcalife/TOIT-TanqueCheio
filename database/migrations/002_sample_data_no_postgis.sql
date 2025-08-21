-- Migration: 002_sample_data_no_postgis.sql
-- Description: Sample data for development and testing (without PostGIS)
-- Created: 2025-08-21

-- Insert sample gas stations in São Paulo
INSERT INTO gas_stations (id, name, brand, address, city, state, postal_code, latitude, longitude, phone, amenities, data_source, data_confidence) VALUES
('11111111-1111-1111-1111-111111111111', 'Posto Shell Paulista', 'Shell', 'Av. Paulista, 1500, Bela Vista', 'São Paulo', 'SP', '01310-100', -23.5618, -46.6565, '+551133334444', '["convenience_store", "restroom", "atm", "car_wash"]', 'manual', 0.9),
('22222222-2222-2222-2222-222222222222', 'Posto Petrobras Faria Lima', 'Petrobras', 'Av. Faria Lima, 2000, Itaim Bibi', 'São Paulo', 'SP', '01451-000', -23.5707, -46.6937, '+551144445555', '["convenience_store", "car_wash", "tire_service"]', 'manual', 0.9),
('33333333-3333-3333-3333-333333333333', 'Posto Ipiranga Vila Olímpia', 'Ipiranga', 'Rua Funchal, 500, Vila Olímpia', 'São Paulo', 'SP', '04551-060', -23.5955, -46.6890, '+551155556666', '["convenience_store", "restroom", "atm"]', 'manual', 0.9),
('44444444-4444-4444-4444-444444444444', 'Posto BR Marginal', 'BR', 'Marginal Tietê, 1000, Barra Funda', 'São Paulo', 'SP', '01140-000', -23.5200, -46.6600, '+551166667777', '["convenience_store", "restaurant", "truck_stop"]', 'manual', 0.8),
('55555555-5555-5555-5555-555555555555', 'Posto Ale Ibirapuera', 'Ale', 'Av. Ibirapuera, 2000, Ibirapuera', 'São Paulo', 'SP', '04029-200', -23.5875, -46.6577, '+551177778888', '["convenience_store", "car_wash"]', 'manual', 0.8),
('66666666-6666-6666-6666-666666666666', 'Posto Shell Berrini', 'Shell', 'Av. Eng. Luís Carlos Berrini, 1000, Brooklin', 'São Paulo', 'SP', '04571-010', -23.6108, -46.6947, '+551188889999', '["convenience_store", "restroom", "atm", "electric_charging"]', 'manual', 0.9),
('77777777-7777-7777-7777-777777777777', 'Posto Petrobras Anhangabaú', 'Petrobras', 'Vale do Anhangabaú, 100, Centro', 'São Paulo', 'SP', '01013-000', -23.5489, -46.6388, '+551199990000', '["convenience_store", "restroom"]', 'manual', 0.7),
('88888888-8888-8888-8888-888888888888', 'Posto Ipiranga Morumbi', 'Ipiranga', 'Av. Giovanni Gronchi, 5000, Morumbi', 'São Paulo', 'SP', '05724-002', -23.6178, -46.7284, '+551100001111', '["convenience_store", "car_wash", "tire_service", "oil_change"]', 'manual', 0.8),
('99999999-9999-9999-9999-999999999999', 'Posto BR Interlagos', 'BR', 'Av. Interlagos, 3000, Interlagos', 'São Paulo', 'SP', '04661-100', -23.6801, -46.6759, '+551111112222', '["convenience_store", "restaurant", "atm"]', 'manual', 0.8),
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Posto Shell Santana', 'Shell', 'Av. Cruzeiro do Sul, 1500, Santana', 'São Paulo', 'SP', '02030-100', -23.5089, -46.6289, '+551122223333', '["convenience_store", "restroom", "car_wash"]', 'manual', 0.9)
ON CONFLICT (id) DO NOTHING;

-- Insert sample fuel prices
INSERT INTO fuel_prices (gas_station_id, fuel_type, price, source, source_confidence, reported_at) VALUES
-- Shell Paulista
('11111111-1111-1111-1111-111111111111', 'gasoline', 5.89, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour'),
('11111111-1111-1111-1111-111111111111', 'ethanol', 4.25, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour'),
('11111111-1111-1111-1111-111111111111', 'diesel', 6.15, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour'),

-- Petrobras Faria Lima
('22222222-2222-2222-2222-222222222222', 'gasoline', 5.75, 'manual_entry', 0.9, NOW() - INTERVAL '2 hours'),
('22222222-2222-2222-2222-222222222222', 'ethanol', 4.19, 'manual_entry', 0.9, NOW() - INTERVAL '2 hours'),
('22222222-2222-2222-2222-222222222222', 'diesel', 6.09, 'manual_entry', 0.9, NOW() - INTERVAL '2 hours'),

-- Ipiranga Vila Olímpia
('33333333-3333-3333-3333-333333333333', 'gasoline', 5.95, 'manual_entry', 0.9, NOW() - INTERVAL '3 hours'),
('33333333-3333-3333-3333-333333333333', 'ethanol', 4.35, 'manual_entry', 0.9, NOW() - INTERVAL '3 hours'),
('33333333-3333-3333-3333-333333333333', 'gnv', 3.89, 'manual_entry', 0.8, NOW() - INTERVAL '3 hours'),

-- BR Marginal
('44444444-4444-4444-4444-444444444444', 'gasoline', 5.82, 'manual_entry', 0.8, NOW() - INTERVAL '4 hours'),
('44444444-4444-4444-4444-444444444444', 'diesel', 6.05, 'manual_entry', 0.8, NOW() - INTERVAL '4 hours'),
('44444444-4444-4444-4444-444444444444', 'diesel_s10', 6.25, 'manual_entry', 0.8, NOW() - INTERVAL '4 hours'),

-- Ale Ibirapuera
('55555555-5555-5555-5555-555555555555', 'gasoline', 5.99, 'manual_entry', 0.8, NOW() - INTERVAL '5 hours'),
('55555555-5555-5555-5555-555555555555', 'ethanol', 4.45, 'manual_entry', 0.8, NOW() - INTERVAL '5 hours'),

-- Shell Berrini
('66666666-6666-6666-6666-666666666666', 'gasoline', 5.79, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour'),
('66666666-6666-6666-6666-666666666666', 'ethanol', 4.15, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour'),
('66666666-6666-6666-6666-666666666666', 'diesel', 6.12, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour'),

-- Petrobras Anhangabaú
('77777777-7777-7777-7777-777777777777', 'gasoline', 6.05, 'manual_entry', 0.7, NOW() - INTERVAL '6 hours'),
('77777777-7777-7777-7777-777777777777', 'ethanol', 4.55, 'manual_entry', 0.7, NOW() - INTERVAL '6 hours'),

-- Ipiranga Morumbi
('88888888-8888-8888-8888-888888888888', 'gasoline', 5.85, 'manual_entry', 0.8, NOW() - INTERVAL '2 hours'),
('88888888-8888-8888-8888-888888888888', 'ethanol', 4.29, 'manual_entry', 0.8, NOW() - INTERVAL '2 hours'),
('88888888-8888-8888-8888-888888888888', 'gnv', 3.95, 'manual_entry', 0.7, NOW() - INTERVAL '2 hours'),

-- BR Interlagos
('99999999-9999-9999-9999-999999999999', 'gasoline', 5.92, 'manual_entry', 0.8, NOW() - INTERVAL '3 hours'),
('99999999-9999-9999-9999-999999999999', 'diesel', 6.18, 'manual_entry', 0.8, NOW() - INTERVAL '3 hours'),

-- Shell Santana
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'gasoline', 5.78, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour'),
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'ethanol', 4.12, 'manual_entry', 0.9, NOW() - INTERVAL '1 hour')
ON CONFLICT DO NOTHING;

-- Insert sample coupons
INSERT INTO coupons (gas_station_id, code, title, description, discount_type, discount_value, fuel_types, valid_from, valid_until, max_uses) VALUES
('11111111-1111-1111-1111-111111111111', 'SHELL10', '10% de desconto na gasolina', 'Desconto de 10% na gasolina comum, válido até o final do mês', 'percentage', 10.00, '["gasoline"]', NOW(), NOW() + INTERVAL '30 days', 1000),
('22222222-2222-2222-2222-222222222222', 'PETRO5', 'R$ 5,00 de desconto', 'Desconto fixo de R$ 5,00 em qualquer combustível', 'fixed_amount', 5.00, NULL, NOW(), NOW() + INTERVAL '15 days', 500),
('33333333-3333-3333-3333-333333333333', 'ETANOL15', '15% OFF no etanol', 'Desconto especial de 15% no etanol', 'percentage', 15.00, '["ethanol"]', NOW(), NOW() + INTERVAL '20 days', 300),
('66666666-6666-6666-6666-666666666666', 'SHELL20', 'R$ 20,00 de desconto', 'Desconto de R$ 20,00 para abastecimentos acima de R$ 100,00', 'fixed_amount', 20.00, NULL, NOW(), NOW() + INTERVAL '25 days', 200),
('88888888-8888-8888-8888-888888888888', 'GNV12', '12% OFF no GNV', 'Desconto especial de 12% no GNV', 'percentage', 12.00, '["gnv"]', NOW(), NOW() + INTERVAL '10 days', 150)
ON CONFLICT (code) DO NOTHING;

-- Insert sample partners
INSERT INTO partners (id, company_name, contact_name, email, phone, api_key, rate_limit_per_hour) VALUES
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Shell Brasil', 'João Silva', 'api@shell.com.br', '+551133334444', 'sk_shell_12345678901234567890', 5000),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Petrobras Distribuidora', 'Maria Santos', 'api@petrobras.com.br', '+551144445555', 'sk_petrobras_09876543210987654321', 3000)
ON CONFLICT (id) DO NOTHING;

-- Update gas stations with partner IDs
UPDATE gas_stations SET partner_id = 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb' WHERE brand = 'Shell';
UPDATE gas_stations SET partner_id = 'cccccccc-cccc-cccc-cccc-cccccccccccc' WHERE brand = 'Petrobras';

-- Log successful migration
INSERT INTO scraping_logs (source_name, scraping_type, status, records_processed, records_success) 
VALUES ('migration', 'sample_data', 'completed', 10, 10);

