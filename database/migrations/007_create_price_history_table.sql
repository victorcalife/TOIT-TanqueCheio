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

-- Comentários para documentação
COMMENT ON TABLE price_history IS 'Histórico de preços para análise de tendências e IA';
COMMENT ON COLUMN price_history.gas_station_id IS 'Referência ao posto de combustível';
COMMENT ON COLUMN price_history.fuel_type IS 'Tipo de combustível';
COMMENT ON COLUMN price_history.price IS 'Preço registrado';
COMMENT ON COLUMN price_history.previous_price IS 'Preço anterior para comparação';
COMMENT ON COLUMN price_history.price_change IS 'Mudança absoluta no preço';
COMMENT ON COLUMN price_history.price_change_percent IS 'Mudança percentual no preço';
COMMENT ON COLUMN price_history.source IS 'Fonte da informação (manual, api, scraping)';

COMMENT ON TABLE market_analysis IS 'Análises estatísticas do mercado de combustíveis';
COMMENT ON COLUMN market_analysis.fuel_type IS 'Tipo de combustível analisado';
COMMENT ON COLUMN market_analysis.region IS 'Região da análise';
COMMENT ON COLUMN market_analysis.volatility_level IS 'Nível de volatilidade dos preços';
COMMENT ON COLUMN market_analysis.trend_direction IS 'Direção da tendência de preços';
COMMENT ON COLUMN market_analysis.trend_strength IS 'Força da tendência (0-100)';

COMMENT ON TABLE price_predictions IS 'Previsões de preços geradas por IA';
COMMENT ON COLUMN price_predictions.predicted_price IS 'Preço previsto pelo algoritmo';
COMMENT ON COLUMN price_predictions.confidence_level IS 'Nível de confiança da previsão (0-100%)';
COMMENT ON COLUMN price_predictions.algorithm_used IS 'Algoritmo usado para a previsão';

