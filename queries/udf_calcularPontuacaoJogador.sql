CREATE FUNCTION dbo.fn_CalcularPontuacaoJogador
(
    @ID_Jogador VARCHAR(16),
    @ID_Jornada VARCHAR(16)
)
RETURNS INT
AS
BEGIN
    DECLARE @Pontuacao INT = 0;
    DECLARE @GolosMarcados INT, @Assistencias INT, @CartoesAmarelos INT,
            @CartoesVermelhos INT, @TempoJogo INT, @GolosSofridos INT;
    DECLARE @Posicao VARCHAR(30);

    -- Obter estatísticas do jogador
    SELECT
        @GolosMarcados = ISNULL(GolosMarcados, 0),
        @Assistencias = ISNULL(Assistencias, 0),
        @CartoesAmarelos = ISNULL(CartoesAmarelos, 0),
        @CartoesVermelhos = ISNULL(CartoesVermelhos, 0),
        @TempoJogo = ISNULL(TempoJogo, 0),
        @GolosSofridos = ISNULL(GolosSofridos, 0)
    FROM FantasyChamp.Pontuação_Jogador
    WHERE ID_jogador = @ID_Jogador AND ID_jornada = @ID_Jornada;

    -- Se não encontrar registo, retorna 0
    IF @GolosMarcados IS NULL
        RETURN 0;

    -- Obter posição do jogador
    SELECT @Posicao = P.Posição
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE J.ID = @ID_Jogador;

    -- Calcular pontos base
    SET @Pontuacao = 0;

    -- Pontos por minutos jogados (1 ponto por 30 minutos)
    IF @TempoJogo >= 30
        SET @Pontuacao = @Pontuacao + (@TempoJogo / 30);

    -- Pontos por golos marcados
    SET @Pontuacao = @Pontuacao + (@GolosMarcados * 5);

    -- Pontos por assistências
    SET @Pontuacao = @Pontuacao + (@Assistencias * 3);

    -- Penalizações por cartões
    SET @Pontuacao = @Pontuacao - (@CartoesAmarelos * 1);
    SET @Pontuacao = @Pontuacao - (@CartoesVermelhos * 3);

    -- Pontos/penalizações específicas por posição
    IF @Posicao = 'Goalkeeper' OR @Posicao = 'Defender'
    BEGIN
        -- Pontos por clean sheet (0 golos sofridos)
        IF @GolosSofridos = 0 AND @TempoJogo >= 60
            SET @Pontuacao = @Pontuacao + 4;

        -- Penalização por golos sofridos
        IF @GolosSofridos > 0
            SET @Pontuacao = @Pontuacao - (@GolosSofridos * 1);
    END

    RETURN @Pontuacao;
END;