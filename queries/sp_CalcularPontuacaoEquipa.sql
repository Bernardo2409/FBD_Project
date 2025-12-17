CREATE PROCEDURE FantasyChamp.CalcularPontuacaoEquipa
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16),
    @PontuacaoTotal INT OUTPUT,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Resultado = 0;
    SET @Mensagem = '';
    SET @PontuacaoTotal = 0;

    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Equipa WHERE ID = @ID_Equipa)
    BEGIN
        SET @Mensagem = 'Equipa não encontrada';
        RETURN;
    END

    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = @ID_Jornada)
    BEGIN
        SET @Mensagem = 'Jornada não encontrada';
        RETURN;
    END

    SELECT @PontuacaoTotal = SUM(CAST(PJ.pontuação_total AS INT))
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    LEFT JOIN FantasyChamp.Pontuação_Jogador PJ
        ON J.ID = PJ.ID_jogador AND PJ.ID_jornada = @ID_Jornada
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 0
      AND ISNUMERIC(PJ.pontuação_total) = 1;

    SET @PontuacaoTotal = ISNULL(@PontuacaoTotal, 0);

    SET @Resultado = 1;
    SET @Mensagem = 'Pontuação calculada com sucesso: ' + CAST(@PontuacaoTotal AS NVARCHAR(10));
END;