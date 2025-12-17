CREATE PROCEDURE sp_ObterEquipaComPontuacoes
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16),
    @PontuacaoTotal INT OUTPUT,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @JogadorID VARCHAR(16);
    DECLARE @PontuacaoJogador INT;
    DECLARE @PontuacaoCalc BIT;
    DECLARE @MensagemCalc NVARCHAR(200);

    -- Tabela temporária para armazenar resultados
    CREATE TABLE #Resultados (
        JogadorID VARCHAR(16),
        Nome NVARCHAR(100),
        Posicao NVARCHAR(50),
        Clube NVARCHAR(100),
        Benched BIT,
        Pontuacao INT,
        ImagemJogador NVARCHAR(255),
        ImagemClube NVARCHAR(255)
    );

    BEGIN TRY
        SET @PontuacaoTotal = 0;

        -- Obter jogadores da equipa
        INSERT INTO #Resultados (JogadorID, Nome, Posicao, Clube, Benched, ImagemJogador, ImagemClube)
        SELECT
            J.ID,
            J.Nome,
            P.Posição,
            C.Nome,
            PE.benched,
            J.jogador_imagem,
            C.clube_imagem
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        WHERE PE.ID_Equipa = @ID_Equipa
        ORDER BY
            CASE WHEN P.Posição = 'Goalkeeper' THEN 1
                 WHEN P.Posição = 'Defender' THEN 2
                 WHEN P.Posição = 'Midfielder' THEN 3
                 WHEN P.Posição = 'Forward' THEN 4
                 ELSE 5 END,
            CASE WHEN PE.benched = 0 THEN 1 ELSE 2 END,
            J.Nome;

        -- Calcular pontuação para cada jogador
        DECLARE cursor_jogadores CURSOR FOR
            SELECT JogadorID FROM #Resultados;

        OPEN cursor_jogadores;
        FETCH NEXT FROM cursor_jogadores INTO @JogadorID;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Calcular pontuação do jogador
            EXEC sp_CalcularPontuacaoJogador
                @ID_Jogador = @JogadorID,
                @ID_Jornada = @ID_Jornada,
                @Pontuacao = @PontuacaoJogador OUTPUT,
                @Resultado = @PontuacaoCalc OUTPUT,
                @Mensagem = @MensagemCalc OUTPUT;

            -- Atualizar tabela temporária
            UPDATE #Resultados
            SET Pontuacao = @PontuacaoJogador
            WHERE JogadorID = @JogadorID;

            -- Somar à pontuação total apenas se não estiver no banco
            IF EXISTS (SELECT 1 FROM #Resultados WHERE JogadorID = @JogadorID AND Benched = 0)
                SET @PontuacaoTotal = @PontuacaoTotal + @PontuacaoJogador;

            FETCH NEXT FROM cursor_jogadores INTO @JogadorID;
        END

        CLOSE cursor_jogadores;
        DEALLOCATE cursor_jogadores;

        -- Retornar resultados
        SELECT * FROM #Resultados
        ORDER BY
            CASE WHEN Posicao = 'Goalkeeper' THEN 1
                 WHEN Posicao = 'Defender' THEN 2
                 WHEN Posicao = 'Midfielder' THEN 3
                 WHEN Posicao = 'Forward' THEN 4
                 ELSE 5 END,
            CASE WHEN Benched = 0 THEN 1 ELSE 2 END,
            Nome;

        SET @Resultado = 1;
        SET @Mensagem = 'Data retrieved successfully';

        -- Limpar tabela temporária
        DROP TABLE #Resultados;

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @PontuacaoTotal = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();

        -- Limpeza em caso de erro
        IF OBJECT_ID('tempdb..#Resultados') IS NOT NULL
            DROP TABLE #Resultados;

        IF CURSOR_STATUS('global', 'cursor_jogadores') >= 0
        BEGIN
            CLOSE cursor_jogadores;
            DEALLOCATE cursor_jogadores;
        END
    END CATCH
END;