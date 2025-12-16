CREATE VIEW FantasyChamp.PontuacaoJogador AS
SELECT
    ID_jogador,
    ID_jornada,
    pontuação_total,
    GolosMarcados,
    Assistencias,
    CartoesAmarelos,
    CartoesVermelhos,
    TempoJogo
FROM FantasyChamp.Pontuação_Jogador;