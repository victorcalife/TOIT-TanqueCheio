-- Migration: Cria as tabelas para o sistema de avaliação de postos e preços.

BEGIN;

-- Tabela para armazenar avaliações de postos de combustível
CREATE TABLE IF NOT EXISTS station_ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    station_id INTEGER NOT NULL REFERENCES gas_stations(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    
    -- Garante que um usuário só pode avaliar um posto uma única vez
    CONSTRAINT _user_station_uc UNIQUE (user_id, station_id)
);

-- Tabela para armazenar validações de preços de combustíveis
CREATE TABLE IF NOT EXISTS price_ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    price_id INTEGER NOT NULL REFERENCES fuel_prices(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('correct', 'incorrect', 'outdated')),
    validated_at TIMESTAMPTZ NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),

    -- Garante que um usuário só pode validar um preço específico uma única vez
    CONSTRAINT _user_price_uc UNIQUE (user_id, price_id)
);

-- Índices para otimizar consultas
CREATE INDEX IF NOT EXISTS idx_station_ratings_station_id ON station_ratings(station_id);
CREATE INDEX IF NOT EXISTS idx_price_ratings_price_id ON price_ratings(price_id);

COMMIT;
