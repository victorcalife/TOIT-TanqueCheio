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

-- Comentários para documentação
COMMENT ON TABLE users IS 'Tabela de usuários do sistema Tanque Cheio';
COMMENT ON COLUMN users.id IS 'ID único do usuário';
COMMENT ON COLUMN users.name IS 'Nome completo do usuário';
COMMENT ON COLUMN users.email IS 'Email único do usuário';
COMMENT ON COLUMN users.phone IS 'Telefone do usuário';
COMMENT ON COLUMN users.password_hash IS 'Hash da senha do usuário';
COMMENT ON COLUMN users.is_active IS 'Status ativo do usuário';
COMMENT ON COLUMN users.created_at IS 'Data de criação do registro';
COMMENT ON COLUMN users.updated_at IS 'Data da última atualização';

