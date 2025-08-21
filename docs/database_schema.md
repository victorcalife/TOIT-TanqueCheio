# Database Schema - Tanque Cheio

## Overview

O banco de dados do Tanque Cheio foi projetado para suportar um sistema completo de recomendações de combustível baseado em GPS, com funcionalidades de autenticação, rastreamento, notificações e parcerias comerciais.

## Architecture

- **Database**: PostgreSQL 15+
- **Extensions**: PostGIS (geospatial operations), uuid-ossp (UUID generation)
- **Coordinate System**: WGS84 (SRID 4326)
- **Indexing**: Spatial indexes (GIST) for location-based queries

## Entity Relationship Diagram

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    users    │────│  user_profiles   │────│  gps_tracking   │
│             │    │                  │    │                 │
│ id (PK)     │    │ id (PK)          │    │ id (PK)         │
│ email       │    │ user_id (FK)     │    │ user_profile_id │
│ password    │    │ fuel_type        │    │ location        │
│ name        │    │ notifications    │    │ trip_id         │
└─────────────┘    │ last_location    │    │ recorded_at     │
                   └──────────────────┘    └─────────────────┘
                            │
                            │
                   ┌──────────────────┐
                   │  notifications   │
                   │                  │
                   │ id (PK)          │
                   │ user_profile_id  │
                   │ gas_station_id   │
                   │ message          │
                   │ sent_at          │
                   └──────────────────┘
                            │
                            │
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  partners   │────│  gas_stations    │────│  fuel_prices    │
│             │    │                  │    │                 │
│ id (PK)     │    │ id (PK)          │    │ id (PK)         │
│ company     │    │ name             │    │ gas_station_id  │
│ api_key     │    │ location         │    │ fuel_type       │
│ rate_limit  │    │ partner_id (FK)  │    │ price           │
└─────────────┘    │ amenities        │    │ reported_at     │
                   └──────────────────┘    └─────────────────┘
                            │
                            │
                   ┌──────────────────┐
                   │     coupons      │
                   │                  │
                   │ id (PK)          │
                   │ gas_station_id   │
                   │ code             │
                   │ discount_value   │
                   │ valid_until      │
                   └──────────────────┘
```

## Core Tables

### users
Tabela principal de autenticação de usuários.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | Email único do usuário |
| password_hash | VARCHAR(255) | Hash da senha (bcrypt) |
| name | VARCHAR(255) | Nome completo |
| phone | VARCHAR(20) | Telefone (opcional) |
| email_verified | BOOLEAN | Status de verificação do email |
| is_active | BOOLEAN | Status ativo/inativo |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Última atualização |

**Indexes:**
- `idx_users_email` on email
- `idx_users_active` on is_active

### user_profiles
Perfis de usuário com preferências de combustível e configurações de notificação.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key para users |
| preferred_fuel_type | VARCHAR(20) | Tipo de combustível preferido |
| notification_enabled | BOOLEAN | Notificações ativadas |
| notification_interval_km | INTEGER | Intervalo de notificação em km |
| notification_radius_km | INTEGER | Raio de busca em km |
| last_location | GEOMETRY(POINT) | Última localização GPS |
| total_distance_km | DECIMAL(10,2) | Distância total percorrida |
| last_notification_km | DECIMAL(10,2) | Km da última notificação |

**Fuel Types:** gasoline, ethanol, gnv, diesel, diesel_s10

**Indexes:**
- `idx_user_profiles_user_id` on user_id
- `idx_user_profiles_fuel_type` on preferred_fuel_type

### gas_stations
Postos de combustível com informações geoespaciais.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(255) | Nome do posto |
| brand | VARCHAR(100) | Marca (Shell, Petrobras, etc.) |
| address | TEXT | Endereço completo |
| city | VARCHAR(100) | Cidade |
| state | VARCHAR(2) | Estado (SP, RJ, etc.) |
| location | GEOMETRY(POINT) | Coordenadas GPS |
| amenities | JSONB | Comodidades disponíveis |
| partner_id | UUID | ID do parceiro (opcional) |
| data_confidence | DECIMAL(3,2) | Confiabilidade dos dados (0-1) |

**Indexes:**
- `idx_gas_stations_location` (GIST) on location
- `idx_gas_stations_brand` on brand
- `idx_gas_stations_city` on (city, state)

### fuel_prices
Preços de combustíveis por posto.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| gas_station_id | UUID | Foreign key para gas_stations |
| fuel_type | VARCHAR(20) | Tipo de combustível |
| price | DECIMAL(6,3) | Preço por litro |
| source | VARCHAR(50) | Fonte dos dados |
| source_confidence | DECIMAL(3,2) | Confiabilidade da fonte |
| reported_at | TIMESTAMP | Data/hora do preço |
| verified_at | TIMESTAMP | Data de verificação |

**Indexes:**
- `idx_fuel_prices_station_fuel` on (gas_station_id, fuel_type)
- `idx_fuel_prices_reported_at` on reported_at DESC

## GPS and Tracking Tables

### gps_tracking
Histórico de rastreamento GPS dos usuários.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_profile_id | UUID | Foreign key para user_profiles |
| location | GEOMETRY(POINT) | Coordenadas GPS |
| accuracy | DECIMAL(8,2) | Precisão em metros |
| speed | DECIMAL(6,2) | Velocidade em km/h |
| trip_id | UUID | ID da viagem |
| distance_from_last | DECIMAL(8,3) | Distância desde último ponto |
| recorded_at | TIMESTAMP | Data/hora do registro |

**Indexes:**
- `idx_gps_tracking_location` (GIST) on location
- `idx_gps_tracking_user_trip` on (user_profile_id, trip_id)

### routes
Rotas calculadas para usuários.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_profile_id | UUID | Foreign key para user_profiles |
| origin_location | GEOMETRY(POINT) | Localização de origem |
| destination_location | GEOMETRY(POINT) | Localização de destino |
| distance_km | DECIMAL(8,2) | Distância total |
| route_geometry | GEOMETRY(LINESTRING) | Geometria da rota |
| estimated_fuel_needed | DECIMAL(6,2) | Combustível estimado |

## Notification System

### notifications
Notificações enviadas aos usuários.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_profile_id | UUID | Foreign key para user_profiles |
| title | VARCHAR(200) | Título da notificação |
| message | TEXT | Conteúdo da mensagem |
| gas_station_id | UUID | Posto recomendado |
| user_location | GEOMETRY(POINT) | Localização do usuário |
| sent_at | TIMESTAMP | Data de envio |
| read_at | TIMESTAMP | Data de leitura |
| clicked_at | TIMESTAMP | Data do clique |

**Indexes:**
- `idx_notifications_user_sent` on (user_profile_id, sent_at DESC)
- `idx_notifications_unread` on user_profile_id WHERE read_at IS NULL

### coupons
Sistema de cupons e vouchers.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| gas_station_id | UUID | Foreign key para gas_stations |
| code | VARCHAR(50) | Código do cupom |
| title | VARCHAR(200) | Título do cupom |
| discount_type | VARCHAR(20) | Tipo: percentage, fixed_amount |
| discount_value | DECIMAL(6,2) | Valor do desconto |
| fuel_types | JSONB | Tipos de combustível válidos |
| valid_until | TIMESTAMP | Data de expiração |
| max_uses | INTEGER | Máximo de usos |

## Partner System

### partners
Contas de parceiros (postos).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| company_name | VARCHAR(255) | Nome da empresa |
| email | VARCHAR(255) | Email de contato |
| api_key | VARCHAR(255) | Chave da API |
| rate_limit_per_hour | INTEGER | Limite de requisições/hora |
| is_active | BOOLEAN | Status ativo |

### price_reports
Relatórios de preços via crowdsourcing.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| fuel_price_id | UUID | Foreign key para fuel_prices |
| user_id | UUID | Usuário que reportou |
| reported_price | DECIMAL(6,3) | Preço reportado |
| report_type | VARCHAR(20) | confirm, dispute, update |
| confidence_level | INTEGER | Nível de confiança (1-5) |
| location | GEOMETRY(POINT) | Localização do report |

## Views

### active_fuel_prices
View com preços ativos dos últimos 7 dias, incluindo informações do posto.

### user_notification_stats
Estatísticas de notificações por usuário (total, lidas, clicadas).

## Performance Considerations

### Spatial Queries
- Todas as consultas geoespaciais usam índices GIST
- Coordenadas armazenadas em WGS84 (SRID 4326)
- Queries otimizadas para busca por proximidade

### Indexing Strategy
- Índices compostos para queries frequentes
- Índices parciais para filtros comuns (is_active = TRUE)
- Índices temporais para dados com timestamp

### Data Retention
- GPS tracking: 90 dias
- Notifications: 1 ano
- Fuel prices: 30 dias para preços inativos
- Scraping logs: 30 dias

## Security

### Data Protection
- Senhas hasheadas com bcrypt
- API keys com expiração
- Tokens JWT com refresh
- Rate limiting por parceiro

### Privacy
- Localização GPS anonimizada após 90 dias
- Dados pessoais criptografados
- Logs de acesso auditáveis

## Backup and Recovery

### Backup Strategy
- Full backup diário
- Incremental backup a cada 6 horas
- Point-in-time recovery habilitado
- Replicação cross-region

### Monitoring
- Query performance monitoring
- Connection pool monitoring
- Disk space alerts
- Slow query logging

