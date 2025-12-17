CREATE PROCEDURE FantasyChamp.sp_ObterEquipaJornadaCompleta
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16),
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @PontuacaoTotal INT = 0;

    BEGIN TRY
        -- 1. Obter lista de jogadores com pontuações
        SELECT
            J.ID AS JogadorID,
            J.Nome AS Nome,
            P.Posição AS Posicao,
            C.Nome AS Clube,
            C.clube_imagem AS ImagemClube,
            J.jogador_imagem AS ImagemJogador,
            PE.benched AS NoBanco,
            ISNULL(PJ.GolosMarcados, 0) AS GolosMarcados,
            ISNULL(PJ.Assistencias, 0) AS Assistencias,
            ISNULL(PJ.CartoesAmarelos, 0) AS CartoesAmarelos,
            ISNULL(PJ.CartoesVermelhos, 0) AS CartoesVermelhos,
            ISNULL(PJ.TempoJogo, 0) AS TempoJogo,
            ISNULL(PJ.pontuação_total, 0) AS Pontuacao  -- Usar da tabela ou calcular
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        LEFT JOIN FantasyChamp.Pontuação_Jogador PJ
            ON J.ID = PJ.ID_Jogador AND PJ.ID_jornada = @ID_Jornada
        WHERE PE.ID_Equipa = @ID_Equipa
        ORDER BY
            CASE WHEN P.Posição = 'Goalkeeper' THEN 1
                 WHEN P.Posição = 'Defender' THEN 2
                 WHEN P.Posição = 'Midfielder' THEN 3
                 WHEN P.Posição = 'Forward' THEN 4
                 ELSE 5 END,
            CASE WHEN PE.benched = 0 THEN 1 ELSE 2 END,
            J.Nome;

        -- 2. Calcular pontuação total (apenas jogadores em campo - benched=0)
        SELECT @PontuacaoTotal = SUM(CAST(ISNULL(PJ.pontuação_total, 0) AS INT))
        FROM FantasyChamp.Pertence PE
        JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
        LEFT JOIN FantasyChamp.Pontuação_Jogador PJ
            ON J.ID = PJ.ID_Jogador AND PJ.ID_jornada = @ID_Jornada
        WHERE PE.ID_Equipa = @ID_Equipa
          AND PE.benched = 0
          AND ISNUMERIC(PJ.pontuação_total) = 1;

        SET @PontuacaoTotal = ISNULL(@PontuacaoTotal, 0);

        -- 3. Retornar pontuação total separadamente
        SELECT @PontuacaoTotal AS PontuacaoTotal;

        SET @Resultado = 1;
        SET @Mensagem = 'Data retrieved successfully';

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();
    END CATCH
END;