ALTER VIEW FantasyChamp.JogadoresEquipa
AS
    SELECT
        J.ID,
        J.Nome,
        P.Posição AS Posicao,
        J.Preço,
        J.jogador_imagem,
        E.Estado,
        PE.ID_Equipa,
        PE.benched,
        C.Nome AS ClubeNome,
        C.clube_imagem
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador  -- INNER JOIN: só jogadores NA equipa
    JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
    JOIN FantasyChamp.Clube C ON J.ID_Clube = C.ID;