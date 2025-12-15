CREATE PROCEDURE sp_ObterDetalhesEquipaParaVisualizacao
    @ID_Equipa UNIQUEIDENTIFIER,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @ID_Utilizador UNIQUEIDENTIFIER;
    DECLARE @NomeEquipa NVARCHAR(100);
    DECLARE @Orcamento DECIMAL(10,2);
    DECLARE @PontuacaoTotal INT;
    DECLARE @NomeUtilizador NVARCHAR(100);
    DECLARE @EmailUtilizador NVARCHAR(100);

    BEGIN TRY
        -- Obter informações básicas da equipa e do utilizador
        SELECT
            @ID_Utilizador = E.ID_utilizador,
            @NomeEquipa = E.Nome,
            @Orcamento = E.Orçamento,
            @PontuacaoTotal = E.PontuaçãoTotal
        FROM FantasyChamp.Equipa E
        WHERE E.ID = @ID_Equipa;

        IF @ID_Utilizador IS NULL
        BEGIN
            SET @Resultado = 0;
            SET @Mensagem = 'Equipa não encontrada';
            RETURN;
        END

        -- Obter informações do utilizador
        SELECT
            @NomeUtilizador = U.PrimeiroNome + ' ' + U.Apelido,
            @EmailUtilizador = U.Email
        FROM FantasyChamp.Utilizador U
        WHERE U.ID = @ID_Utilizador;

        -- Retornar informações da equipa
        SELECT
            @NomeEquipa AS NomeEquipa,
            @Orcamento AS Orcamento,
            @PontuacaoTotal AS PontuacaoTotal,
            @NomeUtilizador AS NomeManager,
            @EmailUtilizador AS EmailManager,
            @ID_Utilizador AS ID_Manager;

        -- Retornar jogadores agrupados por posição
        -- Goalkeepers
        SELECT
            J.ID,
            J.Nome,
            J.Preço,
            J.jogador_imagem,
            P.Posição,
            E.Estado,
            C.Nome AS ClubeNome,
            C.clube_imagem AS ClubeImagem,
            PE.benched
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Goalkeeper'
        ORDER BY
            CASE WHEN PE.benched = 0 THEN 1 ELSE 2 END,
            J.Nome;

        -- Defenders
        SELECT
            J.ID,
            J.Nome,
            J.Preço,
            J.jogador_imagem,
            P.Posição,
            E.Estado,
            C.Nome AS ClubeNome,
            C.clube_imagem AS ClubeImagem,
            PE.benched
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Defender'
        ORDER BY
            CASE WHEN PE.benched = 0 THEN 1 ELSE 2 END,
            J.Nome;

        -- Midfielders
        SELECT
            J.ID,
            J.Nome,
            J.Preço,
            J.jogador_imagem,
            P.Posição,
            E.Estado,
            C.Nome AS ClubeNome,
            C.clube_imagem AS ClubeImagem,
            PE.benched
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Midfielder'
        ORDER BY
            CASE WHEN PE.benched = 0 THEN 1 ELSE 2 END,
            J.Nome;

        -- Forwards
        SELECT
            J.ID,
            J.Nome,
            J.Preço,
            J.jogador_imagem,
            P.Posição,
            E.Estado,
            C.Nome AS ClubeNome,
            C.clube_imagem AS ClubeImagem,
            PE.benched
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Forward'
        ORDER BY
            CASE WHEN PE.benched = 0 THEN 1 ELSE 2 END,
            J.Nome;

        -- Estatísticas
        SELECT
            COUNT(*) AS TotalJogadores,
            SUM(CASE WHEN PE.benched = 0 THEN 1 ELSE 0 END) AS JogadoresCampo,
            SUM(CASE WHEN PE.benched = 1 THEN 1 ELSE 0 END) AS JogadoresBanco,
            SUM(J.Preço) AS ValorTotalEquipa,
            COUNT(DISTINCT C.ID) AS NumeroClubes
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        WHERE PE.ID_Equipa = @ID_Equipa;

        SET @Resultado = 1;
        SET @Mensagem = 'Dados obtidos com sucesso';

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Mensagem = 'Erro: ' + ERROR_MESSAGE();
    END CATCH
END;