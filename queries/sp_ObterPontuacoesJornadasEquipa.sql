CREATE PROCEDURE sp_ObterPontuacoesJornadasEquipa
    @ID_Equipa UNIQUEIDENTIFIER,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Ler da tabela Pontuação_Equipa
        SELECT 
            J.ID AS JornadaID,
            J.Numero AS JornadaNumero,
            ISNULL(PE.pontuação_jornada, 0) AS PontuacaoJornada,
            ISNULL(PE.pontuação_acumulada, 0) AS PontuacaoAcumulada,
            J.Data_Inicio,
            J.Data_Fim
        FROM FantasyChamp.Jornada J
        LEFT JOIN FantasyChamp.Pontuação_Equipa PE 
            ON J.ID = PE.ID_jornada AND PE.ID_Equipa = @ID_Equipa
        ORDER BY J.Numero;
        
        SET @Resultado = 1;
        SET @Mensagem = ''Dados obtidos com sucesso'';
    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Mensagem = ''Erro: '' + ERROR_MESSAGE();
    END CATCH