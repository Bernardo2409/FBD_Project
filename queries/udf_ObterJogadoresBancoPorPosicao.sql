CREATE FUNCTION FantasyChamp.ObterJogadoresBancoPorPosicao
(
    @ID_Equipa UNIQUEIDENTIFIER,
    @Posicao VARCHAR(50)
)
RETURNS TABLE
AS
RETURN
    SELECT
        J.ID,
        J.Nome,
        J.Preço,
        J.jogador_imagem,
        E.Estado
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 1
      AND P.Posição = @Posicao;