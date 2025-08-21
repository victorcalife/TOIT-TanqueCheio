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

-- Comentários para documentação
COMMENT ON TABLE partners IS 'Parceiros comerciais (redes de postos, fornecedores)';
COMMENT ON COLUMN partners.name IS 'Nome do parceiro';
COMMENT ON COLUMN partners.brand IS 'Marca/bandeira do parceiro';
COMMENT ON COLUMN partners.commission_rate IS 'Taxa de comissão do parceiro (0.0500 = 5%)';
COMMENT ON COLUMN partners.contract_start_date IS 'Data de início do contrato';
COMMENT ON COLUMN partners.contract_end_date IS 'Data de fim do contrato';

COMMENT ON TABLE coupons IS 'Cupons de desconto e promoções';
COMMENT ON COLUMN coupons.partner_id IS 'Referência ao parceiro que oferece o cupom';
COMMENT ON COLUMN coupons.gas_station_id IS 'Posto específico (opcional)';
COMMENT ON COLUMN coupons.code IS 'Código único do cupom';
COMMENT ON COLUMN coupons.discount_type IS 'Tipo de desconto (percentage, fixed, per_liter)';
COMMENT ON COLUMN coupons.discount_value IS 'Valor do desconto';
COMMENT ON COLUMN coupons.fuel_type IS 'Tipo de combustível (any para qualquer)';
COMMENT ON COLUMN coupons.min_liters IS 'Quantidade mínima de litros para usar o cupom';
COMMENT ON COLUMN coupons.usage_limit IS 'Limite de usos do cupom';
COMMENT ON COLUMN coupons.usage_count IS 'Quantidade de vezes que foi usado';

COMMENT ON TABLE coupon_usage IS 'Histórico de uso de cupons pelos usuários';
COMMENT ON COLUMN coupon_usage.coupon_id IS 'Referência ao cupom usado';
COMMENT ON COLUMN coupon_usage.user_id IS 'Referência ao usuário que usou';
COMMENT ON COLUMN coupon_usage.liters_purchased IS 'Quantidade de litros comprados';
COMMENT ON COLUMN coupon_usage.discount_applied IS 'Valor do desconto aplicado';
COMMENT ON COLUMN coupon_usage.final_price IS 'Preço final após desconto';

