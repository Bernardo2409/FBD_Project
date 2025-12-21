CREATE VIEW FantasyChamp.JogadorCompleto AS
SELECT
    J.ID,
    J.Nome,
    P.Posição AS Posicao,
    J.Preço,
    J.jogador_imagem,
    E.Estado,
    J.ID_Posição,
    J.ID_Estado_Jogador,
    J.ID_clube
FROM FantasyChamp.Jogador J
JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID;