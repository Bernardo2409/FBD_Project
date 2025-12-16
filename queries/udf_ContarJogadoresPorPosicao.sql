CREATE FUNCTION FantasyChamp.ContarJogadoresPorPosicao
(
    @ID_Equipa UNIQUEIDENTIFIER,
    @Apenas_Campo BIT = 0,
    @Apenas_Banco BIT = 0
)
RETURNS @Result TABLE
(
    Posicao VARCHAR(50),
    Contagem INT
)
AS
BEGIN
    INSERT INTO @Result
    SELECT
        P.Posição,
        COUNT(*) as Contagem
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
    WHERE PE.ID_Equipa = @ID_Equipa
      AND (@Apenas_Campo = 0 OR PE.benched = 0)
      AND (@Apenas_Banco = 0 OR PE.benched = 1)
    GROUP BY P.Posição

    RETURN
END