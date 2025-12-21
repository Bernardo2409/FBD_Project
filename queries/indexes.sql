-- 1. Foreign keys
CREATE NONCLUSTERED INDEX IX_Clube_ID_Pais ON FantasyChamp.Clube(ID_País);
CREATE NONCLUSTERED INDEX IX_Jogador_ID_clube ON FantasyChamp.Jogador(ID_clube);
CREATE NONCLUSTERED INDEX IX_Jogador_ID_Posicao ON FantasyChamp.Jogador(ID_Posição);
CREATE NONCLUSTERED INDEX IX_Jogador_ID_Estado ON FantasyChamp.Jogador(ID_Estado_Jogador);

CREATE NONCLUSTERED INDEX IX_Jogo_ID_Clube1 ON FantasyChamp.Jogo(ID_Clube1);
CREATE NONCLUSTERED INDEX IX_Jogo_ID_Clube2 ON FantasyChamp.Jogo(ID_Clube2);
CREATE NONCLUSTERED INDEX IX_Jogo_ID_jornada ON FantasyChamp.Jogo(ID_jornada);

CREATE NONCLUSTERED INDEX IX_Equipa_ID_utilizador ON FantasyChamp.Equipa(ID_utilizador);

CREATE NONCLUSTERED INDEX IX_Liga_ID_tipoLiga ON FantasyChamp.Liga(ID_tipoLiga);
CREATE NONCLUSTERED INDEX IX_Liga_ID_criador ON FantasyChamp.Liga(ID_criador);

-- 2. Join tables
CREATE NONCLUSTERED INDEX IX_Participa_ID_Liga ON FantasyChamp.Participa(ID_Liga);
CREATE NONCLUSTERED INDEX IX_Pertence_ID_Equipa ON FantasyChamp.Pertence(ID_Equipa);

-- 3. Filtros nas SPs e Views
CREATE NONCLUSTERED INDEX IX_Pertence_benched 
    ON FantasyChamp.Pertence(ID_Equipa, benched) 
    INCLUDE (ID_Jogador);

-- 4. Nas datas para filtros de jogos
CREATE NONCLUSTERED INDEX IX_Jornada_Datas 
    ON FantasyChamp.Jornada(Data_Inicio, Data_Fim) 
    INCLUDE (Numero);

CREATE NONCLUSTERED INDEX IX_Jogo_Data 
    ON FantasyChamp.Jogo(Data) 
    INCLUDE (ID_Clube1, ID_Clube2);

CREATE NONCLUSTERED INDEX IX_Liga_Datas 
    ON FantasyChamp.Liga(Data_Fim, ID_tipoLiga) 
    INCLUDE (Nome, ID_criador);

-- 5. Pontuações, para queries pesadas
CREATE NONCLUSTERED INDEX IX_Pontuacao_Jogador_Lookup 
    ON FantasyChamp.Pontuação_Jogador(ID_jornada, ID_jogador) 
    INCLUDE (pontuação_total, GolosMarcados, Assistencias);

CREATE NONCLUSTERED INDEX IX_Pontuacao_Equipa_Lookup 
    ON FantasyChamp.Pontuação_Equipa(ID_jornada, ID_Equipa) 
    INCLUDE (pontuação_jornada, pontuação_acumulada);