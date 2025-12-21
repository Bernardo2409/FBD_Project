-- ============================================================================
-- Database Initialization Script - FantasyChamp
-- ============================================================================
-- Este script inicializa os dados base essenciais da aplicação.
-- Para popular com dados reais da Champions League, executar: python populate_db.py
-- ============================================================================

USE FantasyChamp;
GO

-- ============================================================================
-- 1. TIPOS DE LIGA (Dados Fixos)
-- ============================================================================
-- Tipos de liga disponíveis no sistema

INSERT INTO FantasyChamp.Tipo_Liga (ID, Tipo) VALUES ('LT01', 'Pública');
INSERT INTO FantasyChamp.Tipo_Liga (ID, Tipo) VALUES ('LT02', 'Privada');
GO

-- ============================================================================
-- 2. POSIÇÕES DOS JOGADORES (Dados Fixos)
-- ============================================================================
-- Posições possíveis para os jogadores

INSERT INTO FantasyChamp.Posição (ID, Posição) VALUES ('POS01', 'Goalkeeper');
INSERT INTO FantasyChamp.Posição (ID, Posição) VALUES ('POS02', 'Defender');
INSERT INTO FantasyChamp.Posição (ID, Posição) VALUES ('POS03', 'Midfielder');
INSERT INTO FantasyChamp.Posição (ID, Posição) VALUES ('POS04', 'Forward');
GO

-- ============================================================================
-- 3. ESTADOS DOS JOGADORES (Dados Fixos)
-- ============================================================================
-- Estados possíveis dos jogadores

INSERT INTO FantasyChamp.Estado_Jogador (ID, Estado) VALUES ('STT01', 'Active');
INSERT INTO FantasyChamp.Estado_Jogador (ID, Estado) VALUES ('STT02', 'On doubt');
INSERT INTO FantasyChamp.Estado_Jogador (ID, Estado) VALUES ('STT03', 'Injured');
INSERT INTO FantasyChamp.Estado_Jogador (ID, Estado) VALUES ('STT04', 'Unavailable');
INSERT INTO FantasyChamp.Estado_Jogador (ID, Estado) VALUES ('STT05', 'Benched');
GO

-- ============================================================================
-- 4. LIGA GLOBAL (Mundial)
-- ============================================================================
-- Liga pública mundial onde todos os utilizadores participam automaticamente

INSERT INTO FantasyChamp.Liga (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_convite)
VALUES (
    '31A96EAE-509D-4E0E-BDE2-6113DF5B3809',
    'Mundial',
    '2025-12-18',
    '2026-05-30',
    'LT01',
    '00000000-0000-0000-0000-000000000000',
    NULL
);
GO

-- ============================================================================
-- 5. DADOS VARIÁVEIS (Populated via Python Script)
-- ============================================================================
-- Os seguintes dados são populados através do script Python populate_db.py:
--
-- PAÍSES (via FlagCDN API):
--   - Código ISO do país
--   - Nome do país
--   - URL da bandeira (https://flagcdn.com/)
--
-- CLUBES (via Football-Data.org API):
--   - 8 clubes da Champions League
--   - Nome, emblema, país
--
-- JOGADORES (via Football-Data.org API):
--   - 15 jogadores por clube (120 total)
--   - Distribuição: 2 GR, 5 Defesas, 5 Médios, 3 Avançados
--   - Nome, posição, preço (4.0-10.0M), clube, estado, foto
--
-- JORNADAS:
--   - 4 jornadas da Champions League
--   - Número, datas de início e fim
--
-- JOGOS:
--   - 16 jogos (4 por jornada)
--   - Resultados aleatórios entre os 8 clubes
--   - Alguns jogos foram posteriormente corrigidos, pois haviam dados duplicados na API
--
-- ESTATÍSTICAS DOS JOGADORES (Pontuação_Jogador):
--   - Tempo de jogo, golos marcados, assistências
--   - Cartões amarelos/vermelhos, golos sofridos
--   - Pontuação total calculada pela fórmula:
--     * +1 ponto por cada 30 minutos jogados
--     * +5 pontos por golo marcado
--     * +3 pontos por assistência
--     * -1 ponto por cartão amarelo
--     * -3 pontos por cartão vermelho
--
-- UTILIZADORES DEMO:
--   - 5 utilizadores de teste
--   - Cada um com equipa completa (15 jogadores: 11 titulares + 4 suplentes)
--   - Respeitam regras: orçamento, máx 3 jogadores/clube, posições obrigatórias
--
-- ============================================================================
-- EXECUÇÃO DO SCRIPT PYTHON
-- ============================================================================
-- Para popular a base de dados com dados reais:
--
-- 1. Configurar ficheiro .env com as credenciais:
--    FOOTBALL_DATA_KEY=your_api_key_here
--    DB_SERVER=localhost
--    DB_NAME=FantasyChamp
--    DB_USER=sa
--    DB_PASSWORD=your_password
--
-- 2. Executar o script:
--    python populate_db.py
--
-- 3. O script irá:
--    - Limpar dados existentes (se confirmado)
--    - Obter dados da Football-Data.org API
--    - Obter bandeiras dos países da RestCountries API
--    - Inserir 8 clubes e 120 jogadores
--    - Criar 4 jornadas com 16 jogos
--    - Gerar estatísticas realistas para todos os jogadores
--    - Criar 5 utilizadores demo com equipas válidas
--
-- ============================================================================
-- APIs UTILIZADAS
-- ============================================================================
--
-- Football-Data.org API:
--   URL: https://api.football-data.org/v4
--   Dados: Clubes, jogadores, calendário da Champions League
--   Autenticação: API Key (tier gratuito)
--
-- FlagCDN API:
--   URL: https://flagcdn.com/
--   Dados: Bandeiras dos países (formato SVG/PNG)
--   Autenticação: Não requerida (API pública)
--
-- ============================================================================

PRINT 'Database initialization complete - Base data inserted';
PRINT 'Run "python populate_db.py" to populate with Champions League data';
GO
