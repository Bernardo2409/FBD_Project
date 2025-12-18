CREATE PROCEDURE FantasyChamp.sp_InserirEstatisticasJogador
    @ID_Jogador VARCHAR(16),
    @ID_Jornada VARCHAR(16),
    @TempoJogo INT,
    @GolosSofridos INT = 0,
    @GolosMarcados INT = 0,
    @Assistencias INT = 0,
    @CartoesAmarelos INT = 0,
    @CartoesVermelhos INT = 0,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Resultado = 0;
    SET @Mensagem = '';

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

    -- Verificar se já existe estatística para este jogador nesta jornada
    IF EXISTS (SELECT 1 FROM FantasyChamp.Pontuação_Jogador 
               WHERE ID_jogador = @ID_Jogador AND ID_jornada = @ID_Jornada)
    BEGIN
        SET @Mensagem = 'Statistics already exist for this player in this round';
        RETURN;
    END

    -- Validar valores (não podem ser negativos)
    IF @TempoJogo < 0 OR @GolosSofridos < 0 OR @GolosMarcados < 0 OR 
       @Assistencias < 0 OR @CartoesAmarelos < 0 OR @CartoesVermelhos < 0
    BEGIN
        SET @Mensagem = 'Statistics values cannot be negative';
        RETURN;
    END

    -- Validar tempo de jogo (máximo 120 minutos incluindo prolongamento)
    IF @TempoJogo > 120
    BEGIN
        SET @Mensagem = 'Playing time cannot exceed 120 minutes';
        RETURN;
    END

    -- Inserir estatísticas (sem calcular pontuação ainda)
    INSERT INTO FantasyChamp.Pontuação_Jogador
        (ID_jogador, ID_jornada, TempoJogo, GolosSofridos, GolosMarcados,
         Assistencias, CartoesAmarelos, CartoesVermelhos, pontuação_total)
    VALUES
        (@ID_Jogador, @ID_Jornada, @TempoJogo, @GolosSofridos, @GolosMarcados,
         @Assistencias, @CartoesAmarelos, @CartoesVermelhos, '0');

    SET @Resultado = 1;
    SET @Mensagem = 'Statistics inserted successfully';
END;
