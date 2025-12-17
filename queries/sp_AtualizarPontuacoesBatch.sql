CREATE PROCEDURE FantasyChamp.sp_AtualizarPontuacoesBatch
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @ID_Equipa UNIQUEIDENTIFIER;
    DECLARE @ID_Jornada VARCHAR(16);
    DECLARE @CountTotal INT = 0;
    DECLARE @R BIT, @M NVARCHAR(200);

    BEGIN TRY
        -- Criar cursor para todas as equipas e jornadas
        DECLARE cursor_equipas_jornadas CURSOR FOR
            SELECT E.ID, J.ID
            FROM FantasyChamp.Equipa E
            CROSS JOIN FantasyChamp.Jornada J
            ORDER BY E.ID, J.ID;

        OPEN cursor_equipas_jornadas;
        FETCH NEXT FROM cursor_equipas_jornadas INTO @ID_Equipa, @ID_Jornada;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Atualizar pontuação para esta equipa e jornada
            EXEC FantasyChamp.AtualizarPontuacaoEquipa
                @ID_Equipa = @ID_Equipa,
                @ID_Jornada = @ID_Jornada,
                @Resultado = @R OUTPUT,
                @Mensagem = @M OUTPUT;

            SET @CountTotal = @CountTotal + 1;

            -- Print progresso a cada 100 registos
            IF @CountTotal % 100 = 0
                PRINT 'Processados ' + CAST(@CountTotal AS NVARCHAR(10)) + ' registos...';

            FETCH NEXT FROM cursor_equipas_jornadas INTO @ID_Equipa, @ID_Jornada;
        END

        CLOSE cursor_equipas_jornadas;
        DEALLOCATE cursor_equipas_jornadas;

        SET @Resultado = 1;
        SET @Mensagem = 'Atualização concluída. ' + CAST(@CountTotal AS NVARCHAR(10)) + ' registos processados.';

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Mensagem = 'Erro: ' + ERROR_MESSAGE();

        -- Fechar cursor se ainda aberto
        IF CURSOR_STATUS('global', 'cursor_equipas_jornadas') >= 0
        BEGIN
            CLOSE cursor_equipas_jornadas;
            DEALLOCATE cursor_equipas_jornadas;
        END
    END CATCH
END;