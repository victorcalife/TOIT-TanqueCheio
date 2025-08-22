-- Migration: Adicionar a coluna CNPJ à tabela gas_stations
--
-- Descrição: Esta migração adiciona uma coluna `cnpj` à tabela `gas_stations`
-- para armazenar o Cadastro Nacional da Pessoa Jurídica de cada posto.
-- A coluna é definida como única para evitar duplicatas e indexada para
-- otimizar as consultas.
--
-- Autor: Cascade
-- Data: 2025-08-22

BEGIN;

-- Adiciona a coluna, permitindo nulos temporariamente para não falhar em tabelas com dados
ALTER TABLE gas_stations
ADD COLUMN cnpj VARCHAR(18);

-- Atualiza registros existentes com um valor placeholder se necessário (opcional)
-- UPDATE gas_stations SET cnpj = 'PREENCHER_CNPJ_' || id WHERE cnpj IS NULL;

-- Adiciona a constraint NOT NULL após a população inicial (se aplicável)
-- ALTER TABLE gas_stations ALTER COLUMN cnpj SET NOT NULL;

-- Cria um índice único na nova coluna para garantir a unicidade e otimizar buscas
CREATE UNIQUE INDEX IF NOT EXISTS idx_gas_stations_cnpj ON gas_stations (cnpj);

COMMIT;

-- Verificação (opcional)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'gas_stations' AND column_name = 'cnpj';
