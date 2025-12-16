CREATE VIEW FantasyChamp.PlayerCompleto AS
SELECT
    J.ID,
    J.Nome,
    P.Posição AS Posicao,
    J.Preço,
    J.jogador_imagem,
    E.Estado,
    C.Nome AS Clube_Nome,
    C.clube_imagem AS Clube_Imagem,
    J.ID_clube,
    J.ID_Posição,
    J.ID_Estado_Jogador
FROM FantasyChamp.Jogador J
JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
LEFT JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID;