-- Adicionar usuário administrador com senha 241286
INSERT INTO users (name, email, phone, password_hash, is_admin, created_at, updated_at)
VALUES (
    'Admin Tanque Cheio', 
    'admin@tanquecheio.app', 
    '+55 47 99999-9999', 
    'scrypt:32768:8:1$pZhJUJidbVMRFxn3$6b6d47a40181b75b19f8ee1f14228fcd65ab4c8fa20b9eba3afde6a878be5d7246d2a8a11089f867ccc3c78209175f9d5d461afe3ed097eb01dc09bb92fbdd3d', 
    TRUE, 
    NOW(), 
    NOW()
);

-- Adicionar perfil para o usuário admin
INSERT INTO user_profiles (user_id, preferred_fuel_type, notification_interval_km, notifications_enabled, last_location_lat, last_location_lng, created_at, updated_at)
VALUES (
    (SELECT id FROM users WHERE email = 'admin@tanquecheio.app'),
    'gasoline',
    100,
    TRUE,
    -26.9187,  -- Balneário Camboriú
    -48.6358,
    NOW(),
    NOW()
);

-- Adicionar usuário de teste com senha 241286
INSERT INTO users (name, email, phone, password_hash, is_admin, created_at, updated_at)
VALUES (
    'João Motorista', 
    'joao.motorista@gmail.com', 
    '+55 47 99999-8888', 
    'scrypt:32768:8:1$pZhJUJidbVMRFxn3$6b6d47a40181b75b19f8ee1f14228fcd65ab4c8fa20b9eba3afde6a878be5d7246d2a8a11089f867ccc3c78209175f9d5d461afe3ed097eb01dc09bb92fbdd3d', 
    FALSE, 
    NOW(), 
    NOW()
);

-- Adicionar perfil para o usuário de teste
INSERT INTO user_profiles (user_id, preferred_fuel_type, notification_interval_km, notifications_enabled, last_location_lat, last_location_lng, created_at, updated_at)
VALUES (
    (SELECT id FROM users WHERE email = 'joao.motorista@gmail.com'),
    'gasoline',
    100,
    TRUE,
    -26.9187,  -- Balneário Camboriú
    -48.6358,
    NOW(),
    NOW()
);

-- Adicionar usuário de teste com senha 241286 (caminhoneiro)
INSERT INTO users (name, email, phone, password_hash, is_admin, created_at, updated_at)
VALUES (
    'Carlos Caminhoneiro', 
    'carlos.caminhoneiro@gmail.com', 
    '+55 47 98765-4321', 
    'scrypt:32768:8:1$pZhJUJidbVMRFxn3$6b6d47a40181b75b19f8ee1f14228fcd65ab4c8fa20b9eba3afde6a878be5d7246d2a8a11089f867ccc3c78209175f9d5d461afe3ed097eb01dc09bb92fbdd3d', 
    FALSE, 
    NOW(), 
    NOW()
);

-- Adicionar perfil para o caminhoneiro (diesel S10, 200km)
INSERT INTO user_profiles (user_id, preferred_fuel_type, notification_interval_km, notifications_enabled, last_location_lat, last_location_lng, created_at, updated_at)
VALUES (
    (SELECT id FROM users WHERE email = 'carlos.caminhoneiro@gmail.com'),
    'diesel_s10',
    200,
    TRUE,
    -26.9187,  -- Balneário Camboriú
    -48.6358,
    NOW(),
    NOW()
);

-- Adicionar usuário de teste com senha 241286 (motociclista)
INSERT INTO users (name, email, phone, password_hash, is_admin, created_at, updated_at)
VALUES (
    'Ana Motociclista', 
    'ana.moto@gmail.com', 
    '+55 47 91234-5678', 
    'scrypt:32768:8:1$pZhJUJidbVMRFxn3$6b6d47a40181b75b19f8ee1f14228fcd65ab4c8fa20b9eba3afde6a878be5d7246d2a8a11089f867ccc3c78209175f9d5d461afe3ed097eb01dc09bb92fbdd3d', 
    FALSE, 
    NOW(), 
    NOW()
);

-- Adicionar perfil para a motociclista (gasolina, 50km)
INSERT INTO user_profiles (user_id, preferred_fuel_type, notification_interval_km, notifications_enabled, last_location_lat, last_location_lng, created_at, updated_at)
VALUES (
    (SELECT id FROM users WHERE email = 'ana.moto@gmail.com'),
    'gasoline',
    50,
    TRUE,
    -26.9187,  -- Balneário Camboriú
    -48.6358,
    NOW(),
    NOW()
);

-- Mensagem de confirmação
SELECT 'Usuários criados com sucesso! Senha para todos: 241286' as message;

