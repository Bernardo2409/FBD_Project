CREATE PROCEDURE FantasyChamp.CalcularPontuacaoJogador
    @ID_Jogador VARCHAR(16),
    @ID_Jornada VARCHAR(16),
    @Pontuacao INT OUTPUT,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Resultado = 0;
    SET @Mensagem = '';
    SET @Pontuacao = 0;

    -- Verificar se o jogador existe
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jogador WHERE ID = @ID_Jogador)
    BEGIN
        SET @Mensagem = 'Player not found';
        RETURN;
    END

    -- Verificar se a jornada existe
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = @ID_Jornada)
    BEGIN
        SET @Mensagem = 'Round not found';
        RETURN;
    END

    -- Obter estatísticas do jogador nesta jornada
    DECLARE @GolosMarcados INT, @Assistencias INT,
            @CartoesAmarelos INT, @CartoesVermelhos INT,
            @TempoJogo INT;

    SELECT
        @GolosMarcados = ISNULL(GolosMarcados, 0),
        @Assistencias = ISNULL(Assistencias, 0),
        @CartoesAmarelos = ISNULL(CartoesAmarelos, 0),
        @CartoesVermelhos = ISNULL(CartoesVermelhos, 0),
        @TempoJogo = ISNULL(TempoJogo, 0)
    FROM FantasyChamp.Pontuação_Jogador
    WHERE ID_jogador = @ID_Jogador AND ID_jornada = @ID_Jornada;

    IF @GolosMarcados IS NULL
    BEGIN
        SET @Pontuacao = 0;
        SET @Resultado = 1;
        SET @Mensagem = 'Player has no statistics for this round';
        RETURN;
    END

    SET @Pontuacao =
        (@GolosMarcados * 5) +
        (@Assistencias * 3) -
        (@CartoesAmarelos * 1) -
        (@CartoesVermelhos * 3);

    IF @TempoJogo >= 60
        SET @Pontuacao = @Pontuacao + 2;
    ELSE IF @TempoJogo >= 30
        SET @Pontuacao = @Pontuacao + 1;

    IF @Pontuacao < 0
        SET @Pontuacao = 0;

    SET @Resultado = 1;
    SET @Mensagem = 'Pontuation calculated successfully';
END;