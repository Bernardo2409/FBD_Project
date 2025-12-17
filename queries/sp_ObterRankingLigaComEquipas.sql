CREATE PROCEDURE sp_ObterRankingLigaComEquipas
    @ID_Liga UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16) = NULL,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        IF @ID_Jornada IS NULL
        BEGIN
            -- Ranking geral (soma de todas as jornadas) - apenas com equipas
            SELECT
                ROW_NUMBER() OVER (ORDER BY E.PontuaçãoTotal DESC) AS posicao,
                U.PrimeiroNome + ' ' + U.Apelido AS nome_utilizador,
                E.Nome AS nome_equipa,
                E.PontuaçãoTotal AS pontuacao_acumulada,
                E.ID AS id_equipa,
                E.ID_utilizador AS id_utilizador,
                0 AS pontuacao  -- Coluna dummy para compatibilidade
            FROM FantasyChamp.Participa P
            JOIN FantasyChamp.Utilizador U ON P.ID_Utilizador = U.ID
            INNER JOIN FantasyChamp.Equipa E ON U.ID = E.ID_utilizador
            WHERE P.ID_Liga = @ID_Liga
            ORDER BY E.PontuaçãoTotal DESC, U.PrimeiroNome;
        END
        ELSE
        BEGIN
            -- Ranking por jornada específica - apenas com equipas
            SELECT
                ROW_NUMBER() OVER (ORDER BY ISNULL(PE.pontuação_jornada, 0) DESC) AS posicao,
                U.PrimeiroNome + ' ' + U.Apelido AS nome_utilizador,
                E.Nome AS nome_equipa,
                ISNULL(PE.pontuação_jornada, 0) AS pontuacao,
                ISNULL(PE.pontuação_acumulada, 0) AS pontuacao_acumulada,
                E.ID AS id_equipa,
                E.ID_utilizador AS id_utilizador
            FROM FantasyChamp.Participa P
            JOIN FantasyChamp.Utilizador U ON P.ID_Utilizador = U.ID
            INNER JOIN FantasyChamp.Equipa E ON U.ID = E.ID_utilizador
            LEFT JOIN FantasyChamp.Pontuação_Equipa PE
                ON E.ID = PE.ID_equipa AND PE.ID_jornada = @ID_Jornada
            WHERE P.ID_Liga = @ID_Liga
            ORDER BY ISNULL(PE.pontuação_jornada, 0) DESC, U.PrimeiroNome;
        END

        SET @Resultado = 1;
        SET @Mensagem = 'Ranking obtained successfully';

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();
    END CATCH
END;