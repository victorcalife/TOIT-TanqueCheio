Quebra de Tarefas Detalhada - Aplicativo de Indicação de Menores Preços de Combustíveis
Data: 21 de agosto de 2025
Versão: 1.0

Sumário Executivo
Este documento apresenta a decomposição detalhada de todas as funcionalidades do aplicativo em épicos, histórias de usuário, tasks técnicas e subtasks específicas. A estrutura segue metodologia ágil com estimativas em story points, critérios de aceitação claros, e dependências mapeadas para facilitar o planejamento de sprints.

A organização hierárquica permite visibilidade desde o nível estratégico (épicos) até o nível operacional (subtasks), facilitando tanto o planejamento de releases quanto a execução diária das equipes de desenvolvimento. Cada item inclui prioridade, complexidade estimada, e responsável técnico sugerido.

Estrutura de Organização
Hierarquia de Tarefas
Épicos: Grandes funcionalidades que agregam valor significativo ao usuário e podem ser entregues de forma independente.

Histórias de Usuário: Funcionalidades específicas descritas da perspectiva do usuário final, com valor de negócio claro.

Tasks: Atividades técnicas necessárias para implementar uma história de usuário.

Subtasks: Atividades granulares que compõem uma task, atribuíveis a desenvolvedores individuais.

Sistema de Priorização
P0 - Crítico: Funcionalidades essenciais para MVP, sem as quais o produto não pode ser lançado. P1 - Alto: Funcionalidades importantes para experiência completa do usuário. P2 - Médio: Funcionalidades que melhoram significativamente a experiência. P3 - Baixo: Funcionalidades nice-to-have que podem ser postergadas.

# ÉPICO 1: Infraestrutura e Arquitetura Base
Prioridade: P0 - Crítico
Responsável: Manus / Victor

Descrição do Épico
Estabelecimento da infraestrutura tecnológica fundamental que suportará todas as funcionalidades do aplicativo. Inclui configuração de ambientes, implementação da arquitetura de microserviços, setup de banco de dados, e estabelecimento de pipelines de CI/CD.

História de Usuário 1.1: Setup de Infraestrutura Cloud
Como Victor Eu quero ter ambientes de desenvolvimento, staging e produção configurados
Para que eu possa desenvolver e deployar o aplicativo de forma segura e eficiente

Prioridade: P0

Critérios de Aceitação:

Ambientes dev, staging e prod configurados no Railway
PostgreSQL SQL Puro com arquivos de migração que serão executados pelo Victor, configurado em todos os ambientes
Redis configurado para cache e message queues
Monitoramento básico implementado
Backup automatizado configurado
Tasks:

## Task 1.1.1: Configuração Railway e Ambientes

Responsável: Victor Calife
Subtasks:
- [X] Criar conta e configurar projeto no Railway (Responsável: Victor)
-- Project ID = 88f96c77-caa5-4f8b-aebd-79015a2e8901

- [X] Configurar ambiente development e production (Responsável: Victor)
-- Ambientes criados: development e production

- [X] Configurar variáveis de ambiente (Responsável: Victor)
--ambiente development:
---Backend: API_URL=backend-tc-development.up.railway.app  | DATABASE_URL=postgresql://postgres:WWyaQJVrqJqmryQNcKdIyQBjGsPIbsXJ@postgres.railway.internal:5432/railway  |  NODE_ENV=development |  PORT=8080
            JWT_SECRET=ASdWQOdoiasjdwh212ajd302roifao  |  REDIS_URL=redis://default:RxEKdfxmBpTrfniWWjMCfdvQOWTrmeFB@redis.railway.internal:6379 | SESSION_SECRET=douwoudhaoqp1223AOID0132d283fnoied
---Frontend: API_URL=backend-tc-development.up.railway.app | NODE_ENV=development |  PORT=8080

--ambiente production:
---Backend: API_URL=betc-production.up.railway.app  | DATABASE_URL=postgresql://postgres:************@postgres-admt.railway.internal:5432/railway  |  NODE_ENV=production  |  PORT=8080
            JWT_SECRET=***********  |  REDIS_URL=redis://default:***********@redis-uwuw.railway.internal:6379 | SESSION_SECRET=*********
---Frontend: API_URL=betc-production.up.railway.app | NODE_ENV=production |  PORT=8080

- [X] Configurar domínios customizados (Responsável: Victor)
--ambiente development:
---Backend: backend-tc-development.up.railway.app
---Frontend: frontend-tc-development.up.railway.app

--ambiente production:
---Backend: betc-production.up.railway.app
---Frontend: fetc-production.up.railway.app

- [X] Documentar processo de deploy (Responsável: Victor)
--Ambiente development possui os serviços de frontend e backend conectados à branch dev (já criada) no repositório do github https://github.com/victorcalife/TOIT-TanqueCheio.git.
--Serviço backend possui root backend e serviço frontend possui root frontend.

--Ambiente production possui os serviços de frontend e backend conectados à branch main (já criada) no repositório do github https://github.com/victorcalife/TOIT-TanqueCheio.git.
--Serviço backend possui root backend e serviço frontend possui root frontend.

De hoje e até golive, deploy deve ser feito para as duas branchs e atualizar os dois ambientes simultaneamente. Foram criados banco de dados distintos e, após golive, os pushs e deploys passam a acontecer apenas em dev e atualização em main após validação e aprovação.


Task 1.1.2: Setup PostgreSQL Railway SQL Puro com Migraçoes

Responsável: Victor/Manus
Subtasks:
- [X] Configurar instâncias PostgreSQL (Responsável: Victor)
--Ambiente development railway: Postgres Public: postgresql://postgres:WWyaQJVrqJqmryQNcKdIyQBjGsPIbsXJ@interchange.proxy.rlwy.net:16420/railway
--Ambiente production railway: Postgres Public: postgresql://postgres:************@postgres-admt.railway.internal:5432/railway

- [ ] Instalar e configurar extensão PostGIS (Responsável: Manus)
- [ ] Criar schemas iniciais (Responsável: Manus)
- [ ] Configurar usuários e permissões (Responsável: Manus)
- [ ] Implementar scripts de migração (Responsável: Manus)

## Task 1.1.3: Configuração Redis

Responsável: Manus/Victor
Subtasks:
- [X] Configurar instâncias Redis (Responsável: Victor)
--Ambiente development railway: Redis Public: redis://default:RxEKdfxmBpTrfniWWjMCfdvQOWTrmeFB@nozomi.proxy.rlwy.net:16784
--Ambiente production railway: Redis Public: redis://default:***********@redis-uwuw.railway.internal:6379

- [ ] Configurar clustering se necessário (Responsável: Manus)
- [ ] Implementar health checks (Responsável: Manus)
- [ ] Configurar persistência (Responsável: Manus)

## Task 1.1.4: Monitoramento e Logs

Responsável: Manus
- [ ] Configurar logging centralizado
- [ ] Implementar métricas completas
- [ ] Configurar alertas críticos
- [ ] Setup dashboards profissionais

História de Usuário 1.2: API Gateway e Autenticação
Como usuário do aplicativo
Eu quero fazer login de forma segura
Para que eu possa acessar funcionalidades personalizadas e fazer minhas configuraçoes para receber as notificações que fazem sentido para mim, que realmente estarão dentro dos parâmetros da minha rota e que de forma verídica sejam 100% verdadeiras.

Prioridade: P0

Critérios de Aceitação:

API Gateway implementado com rate limiting
Sistema de autenticação JWT implementado
Endpoints de registro e login funcionais
Middleware de autorização implementado
Documentação de API gerada automaticamente
Tasks:

## Task 1.2.1: Implementação API Gateway

Responsável: Manus
Subtasks:
- [ ] Setup Express.js com middleware completo
- [ ] Implementar rate limiting
- [ ] Configurar CORS completo
- [ ] Implementar logging de requests
- [ ] Configurar health check endpoints

## Task 1.2.2: Sistema de Autenticação

Responsável: Manus
Subtasks:
- [ ] Implementar geração e validação JWT
- [ ] Criar endpoints de registro/login
- [ ] Implementar hash de senhas
- [ ] Configurar refresh tokens
- [ ] Implementar logout e blacklist

## Task 1.2.3: Middleware de Autorização

Responsável: Manus
Subtasks:
- [ ] Implementar middleware de autenticação
- [ ] Criar sistema de roles e permissões
- [ ] Implementar decorators para proteção de rotas
C- [ ] onfigurar tratamento de erros

História de Usuário 1.3: CI/CD Pipeline
Neste momento, CI/CD básico atualizando as duas branchs (dev e main) simultaneamente. Servicos dos ambientes development e production da railway ja estou apontando para branchs corretas e roots corretos (fronend e backend)

Prioridade: P0

Critérios de Aceitação:

Pipeline de CI/CD configurado no GitHub Actions

Deploy automático para main 

Tasks:

## Task 1.3.1: GitHub Actions Setup
- [ ] Implementar notificações push/deploy simultaneo para dev e main (deploy automatico na railway)

## Task 1.3.2: Testes Automatizados

Responsável: Manus
Subtasks:
- [ ] Configurar Jest para testes unitários
- [ ] Implementar testes de integração 
- [ ] Configurar coverage reports
- [ ] Implementar quality gates

História de Usuário 1.4: Documentação Técnica Base
Como Manus Eu quero ter documentação técnica atualizada
Para que eu possa entender e contribuir com o projeto eficientemente

Prioridade: P1

Critérios de Aceitação:

README.md completo com setup instructions
Documentação de API gerada automaticamente
Guias de contribuição e coding standards
Documentação de arquitetura atualizada
Tasks:

## Task 1.4.1: Documentação de Setup

Responsável: Manus
Subtasks:
- [ ] Criar README.md detalhado
- [ ] Documentar processo de setup local
- [ ] Criar guias de troubleshooting
- [ ] Documentar variáveis de ambiente

##Task 1.4.2: Documentação de API

Responsável: Manus
- [ ] Configurar Swagger/OpenAPI
- [ ] Documentar todos os endpoints
- [ ] Implementar geração automática
- [ ] Criar exemplos de uso


#ÉPICO 2: Integração com APIs de Navegação
Prioridade: P0 - Crítico

Descrição do Épico
Implementação das integrações fundamentais com Google Maps API e outras APIs de navegação para obter informações de rotas, geocoding, e places search. Inclui otimizações de performance, cache inteligente, e fallbacks para garantir disponibilidade.

História de Usuário 2.1: Integração Google Maps API
Como Manus
Eu quero inserir origem e destino
Para que o sistema possa calcular minha rota e encontrar postos no caminho

Prioridade: P0

Critérios de Aceitação:

Faz uso das informaçoes dos apps de gps já utilizados (waze, google maps, etc) 
Geocoding de endereços funcionando
Identificação de pontos de interesse (postos) na rota
Distância total até o local indicado com combustível mais barato
Tasks:

## Task 2.1.1: Setup Google Maps API

Responsável: Manus
Subtasks:
- [ ] Ativar APIs necessárias (Maps, waze, etc)
- [ ] Configurar billing e quotas
- [ ] Implementar autenticação API
- [ ] Configurar rate limiting

## Task 2.1.2: Serviço de Geocoding

Responsável: Manus
Subtasks:
- [ ] Implementar endpoint de geocoding
- [ ] Adicionar validação de endereços
- [ ] Implementar cache de resultados
- [ ] Tratar erros e fallbacks
- [ ] Implementar testes unitários

## Task 2.1.3: Serviço de Roteamento

Responsável: Manus
Subtasks:
- [ ] Implementar cálculo/leitura de rotas conforme app de gps utilizado pelo motorista no momento da viagem/trajeto/deslocamento
- [ ] Suportar diferentes tipos de apps/rotas
- [ ] Implementar raio de busca configurável Suportar distâncias diferentes paa envio das notificações/informações conforme configuração de cada usuário. Definir opções de distâncias (50km | 150km | 300km | 500km)
- [ ]Implementar waypoints
- [ ]Otimizar chamadas de API

## Task 2.1.4: Identificação de POIs

Responsável: Manus
Subtasks:
- [ ] Implementar busca de postos na rota / utilizar serviço de GPS do app é uma opção
- [ ] Filtrar por tipo de combustível escolhido pelo usuário



ÉPICO 3: Sistema de Coleta e Gestão de Preços
Prioridade: P0 - Crítico
Responsável: Manus

Descrição do Épico
Desenvolvimento do sistema core de coleta, validação, e gestão de preços de combustíveis. Inclui múltiplas fontes de dados, algoritmos de validação, crowdsourcing, e APIs para parceiros.

História de Usuário 3.1: Web Scraping de Fontes Públicas
Como sistema
Eu quero coletar preços de fontes públicas confiáveis
Para que eu possa ter uma base de dados abrangente de preços

Prioridade: P0

Critérios de Aceitação:

Scrapers e buscas para pelo menos 10 postos/pois identificados na rota de deslocamento do usuário
Dados normalizados e estruturados
Agendamento automático de coletas
Tratamento de mudanças em estruturas de sites
Logs detalhados de coletas
Tasks:

## Task 3.1.1: Framework de Web Scraping

Responsável: Manus
Subtasks:
- [ ]Setup Scrapy, pesquisa ou similar
- [ ] Implementar base classes para scrapers, pesquisas, etc
- [ ]Configurar proxy rotation
- [ ]Implementar rate limiting
- [ ]Adicionar tratamento de erros

## Task 3.1.2: Normalização de Dados

Responsável: Manus
Subtasks:
- [ ]Implementar pipeline de normalização
- [ ]Padronizar formatos de endereços
- [ ]Normalizar tipos de combustível
- [ ]Configurar deduplicação

História de Usuário 3.2: APIs para Parceiros
Como posto de combustível parceiro
Eu quero enviar meus preços via API
Para que eles sejam exibidos em tempo real no aplicativo

Prioridade: P0

Critérios de Aceitação:

API REST para recebimento de preços
Autenticação e autorização para parceiros
Validação automática de dados recebidos
Dashboard para parceiros visualizarem dados
Documentação completa da API
Tasks:

## Task 3.2.1: API de Parceiros

Responsável: Manus
Subtasks:
- [ ] Implementar endpoints de API
- [ ] Configurar autenticação por API key
- [ ] Implementar validação de dados
- [ ] Adicionar rate limiting por parceiro
- [ ] Implementar logs de auditoria

## Task 3.2.2: Dashboard para Parceiros

Responsável: Manus
Subtasks:
- [ ] Criar interface de login
- [ ] Implementar dashboard de métricas
- [ ] Adicionar formulário de atualização de preços
- [ ] Implementar histórico de atualizações
- [ ] Adicionar relatórios básicos

História de Usuário 3.3: Sistema de Validação e Qualidade
Como Manus
Eu quero ter certeza de que os preços estão corretos
Para que eu possa confiar nas recomendações do aplicativo

Prioridade: P0

Critérios de Aceitação:

Algoritmos de detecção de anomalias
Validação cruzada entre fontes
Sistema de scoring de confiabilidade
Crowdsourcing para validação
Alertas para dados suspeitos
Tasks:

## Task 3.3.1: Algoritmos de Validação

Responsável: Manus
Subtasks:
- [ ] Implementar detecção de outliers
- [ ] Criar regras de validação por região
- [ ] Implementar comparação temporal
- [ ] Configurar thresholds automáticos
- [ ] Implementar machine learning básico

## Task 3.3.2: Sistema de Crowdsourcing

Responsável: Manus
Subtasks:
- [ ] Implementar endpoints para reports
- [ ] Criar interface mobile para reports
- [ ] Implementar sistema de reputação para postos parceiros
- [ ] Implementar moderação automática
