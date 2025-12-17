CREATE PROCEDURE FantasyChamp.AtualizarPontuacaoEquipa
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16),
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Resultado = 0;
    SET @Mensagem = '';

    -- 1. Verificar se a equipa existe
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Equipa WHERE ID = @ID_Equipa)
    BEGIN
        SET @Mensagem = 'Team not found';
        RETURN;
    END

    -- 2. Verificar se a jornada existe
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = @ID_Jornada)
    BEGIN
        SET @Mensagem = 'Round not found';
        RETURN;
    END

    -- 3. Calcular pontuação da equipa
    DECLARE @PontuacaoJornada INT;

    -- Chama a SP que já criamos
    DECLARE @R BIT, @M NVARCHAR(200);

    EXEC FantasyChamp.CalcularPontuacaoEquipa
        @ID_Equipa = @ID_Equipa,
        @ID_Jornada = @ID_Jornada,
        @PontuacaoTotal = @PontuacaoJornada OUTPUT,
        @Resultado = @R OUTPUT,
        @Mensagem = @M OUTPUT;

    IF @R = 0
    BEGIN
        SET @Mensagem = @M;
        RETURN;
    END

    -- 4. Atualizar tabela Pontuação_Equipa
    IF EXISTS (SELECT 1 FROM FantasyChamp.Pontuação_Equipa
               WHERE ID_Equipa = @ID_Equipa AND ID_jornada = @ID_Jornada)
    BEGIN
        -- Atualizar
        UPDATE FantasyChamp.Pontuação_Equipa
        SET pontuação_jornada = @PontuacaoJornada
        WHERE ID_Equipa = @ID_Equipa AND ID_jornada = @ID_Jornada;
    END
    ELSE
    BEGIN
        -- Inserir
        INSERT INTO FantasyChamp.Pontuação_Equipa
            (ID_Equipa, ID_jornada, pontuação_jornada)
        VALUES
            (@ID_Equipa, @ID_Jornada, @PontuacaoJornada);
    END

    SET @Resultado = 1;
    SET @Mensagem = 'Pontuation updated successfully: ' + CAST(@PontuacaoJornada AS NVARCHAR(10));
END;