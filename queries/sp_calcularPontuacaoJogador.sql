CREATE PROCEDURE sp_CalcularPontuacaoJogador
    @ID_Jogador VARCHAR(16),
    @ID_Jornada VARCHAR(16),
    @Pontuacao INT OUTPUT,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        -- Calcular pontuação usando a função
        SET @Pontuacao = dbo.fn_CalcularPontuacaoJogador(@ID_Jogador, @ID_Jornada);

        -- Atualizar a tabela Pontuação_Jogador
        IF EXISTS (SELECT 1 FROM FantasyChamp.Pontuação_Jogador
                  WHERE ID_jogador = @ID_Jogador AND ID_jornada = @ID_Jornada)
        BEGIN
            UPDATE FantasyChamp.Pontuação_Jogador
            SET pontuação_total = @Pontuacao
            WHERE ID_jogador = @ID_Jogador AND ID_jornada = @ID_Jornada;
        END
        ELSE
        BEGIN
            -- Inserir novo registo com pontuação calculada
            INSERT INTO FantasyChamp.Pontuação_Jogador
                (ID_jogador, ID_jornada, pontuação_total)
            VALUES
                (@ID_Jogador, @ID_Jornada, @Pontuacao);
        END

        SET @Resultado = 1;
        SET @Mensagem = 'Pontuação calculada e atualizada com sucesso';

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Pontuacao = 0;
        SET @Mensagem = 'Erro: ' + ERROR_MESSAGE();
    END CATCH
END;