CREATE FUNCTION FantasyChamp.fn_ObterPosicaoJogador
    (@ID_Jogador UNIQUEIDENTIFIER)
RETURNS VARCHAR(50)
AS
BEGIN
    DECLARE @Posicao VARCHAR(50);

    SELECT @Posicao = P.Posição
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE J.ID = @ID_Jogador;

    RETURN @Posicao;
END;