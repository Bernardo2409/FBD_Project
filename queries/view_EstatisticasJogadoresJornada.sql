CREATE VIEW FantasyChamp.EstatisticasJogadoresJornada
AS
    SELECT
        PJ.ID_jornada,
        PJ.ID_jogador,
        J.Nome,
        P.Posição AS Posicao,
        J.jogador_imagem,
        C.Nome AS Clube,
        C.ID AS Clube_ID,
        PJ.GolosMarcados,
        PJ.Assistencias,
        PJ.CartoesAmarelos,
        PJ.CartoesVermelhos,
        PJ.TempoJogo,
        PJ.pontuação_total
    FROM FantasyChamp.Pontuação_Jogador PJ
    JOIN FantasyChamp.Jogador J ON PJ.ID_jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID;