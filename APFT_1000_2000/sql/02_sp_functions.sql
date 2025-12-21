CREATE PROCEDURE FantasyChamp.AbandonarLiga
    @ID_Utilizador UNIQUEIDENTIFIER,
    @ID_Liga UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    DELETE FROM FantasyChamp.Participa
    WHERE ID_Utilizador = @ID_Utilizador
      AND ID_Liga = @ID_Liga;
END;

CREATE PROCEDURE sp_AdicionarJogadorEquipa
    @ID_Equipa UNIQUEIDENTIFIER,       -- GUID
    @ID_Jogador VARCHAR(16),           -- VARCHAR(16)
    @Resultado INT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;

    DECLARE @Preco DECIMAL(10,2);
    DECLARE @Orcamento DECIMAL(10,2);
    DECLARE @Posicao NVARCHAR(50);
    DECLARE @TotalBanco INT;
    DECLARE @ContadorGR_Banco INT;
    DECLARE @ContadorAvancados_Banco INT;
    DECLARE @ContadorAvancados_Campo INT;
    DECLARE @TotalAvancados INT;
    DECLARE @BenchedStatus BIT;
    DECLARE @ContadorPosicao_Banco INT;

    -- Verificar se já existe
    IF EXISTS (SELECT 1 FROM FantasyChamp.Pertence
               WHERE ID_Equipa = @ID_Equipa AND ID_Jogador = @ID_Jogador)
    BEGIN
        SET @Resultado = 0;
        SET @Mensagem = 'Player already in team';
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Obter preço e posição do jogador
    SELECT @Preco = J.Preço, @Posicao = P.Posição
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE J.ID = @ID_Jogador;

    IF @Preco IS NULL OR @Posicao IS NULL
    BEGIN
        SET @Resultado = 0;
        SET @Mensagem = 'Player not found';
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Verificar orçamento
    SELECT @Orcamento = Orçamento FROM FantasyChamp.Equipa WHERE ID = @ID_Equipa;

    IF @Orcamento < @Preco
    BEGIN
        SET @Resultado = 0;
        SET @Mensagem = 'Insufficient money';
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Contar jogadores no banco
    SELECT @TotalBanco = COUNT(*)
    FROM FantasyChamp.Pertence
    WHERE ID_Equipa = @ID_Equipa AND benched = 1;

    -- Contar GR no banco
    SELECT @ContadorGR_Banco = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 1
      AND P.Posição = 'Goalkeeper';

    -- Contar avançados no banco
    SELECT @ContadorAvancados_Banco = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 1
      AND P.Posição = 'Forward';

    -- Contar avançados em campo
    SELECT @ContadorAvancados_Campo = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 0
      AND P.Posição = 'Forward';

    -- Contar jogadores da mesma posição no banco
    SELECT @ContadorPosicao_Banco = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 1
      AND P.Posição = @Posicao;

    -- Lógica de atribuição banco/campo
    -- NOVA LÓGICA CORRETA: Primeiro preenche o CAMPO, depois o BANCO
    SET @BenchedStatus = 0; -- Default: vai para CAMPO (invertido!)
    
    DECLARE @ContadorGR_Total INT;
    DECLARE @ContadorDefesas_Total INT;
    DECLARE @ContadorMedios_Total INT;
    DECLARE @ContadorAvancados_Total INT;
    
    -- Contar totais de cada posição
    SELECT @ContadorGR_Total = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Goalkeeper';
    
    SELECT @ContadorDefesas_Total = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Defender';
    
    SELECT @ContadorMedios_Total = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Midfielder';
    
    SELECT @ContadorAvancados_Total = COUNT(*)
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE PE.ID_Equipa = @ID_Equipa AND P.Posição = 'Forward';
    
    -- REGRAS CORRETAS: O último de cada posição vai para o banco
    -- GR: 2 total (1º campo, 2º banco)
    IF @Posicao = 'Goalkeeper'
    BEGIN
        IF @ContadorGR_Total >= 1  -- Já tem 1 GR (no campo)
            SET @BenchedStatus = 1; -- 2º GR vai para o banco
        ELSE
            SET @BenchedStatus = 0; -- 1º GR vai para o campo
    END
    
    -- Defesas: 5 total (primeiros 4 campototal, 5º banco)
    ELSE IF @Posicao = 'Defender'
    BEGIN
        IF @ContadorDefesas_Total >= 4  -- Já tem 4 defesas (no campo)
            SET @BenchedStatus = 1; -- 5º defesa vai para o banco
        ELSE
            SET @BenchedStatus = 0; -- Primeiros 4 vão para o campo
    END
    
    -- Médios: 5 total (primeiros 4 campo, 5º banco)
    ELSE IF @Posicao = 'Midfielder'
    BEGIN
        IF @ContadorMedios_Total >= 4  -- Já tem 4 médios (no campo)
            SET @BenchedStatus = 1; -- 5º médio vai para o banco
        ELSE
            SET @BenchedStatus = 0; -- Primeiros 4 vão para o campo
    END
    
    -- Avançados: 3 total (primeiros 2 campo, 3º banco)
    ELSE IF @Posicao = 'Forward'
    BEGIN
        IF @ContadorAvancados_Total >= 2  -- Já tem 2 avançados (no campo)
            SET @BenchedStatus = 1; -- 3º avançado vai para o banco
        ELSE
            SET @BenchedStatus = 0; -- Primeiros 2 vão para o campo
    END

    -- Inserir jogador
    INSERT INTO FantasyChamp.Pertence (ID_Equipa, ID_Jogador, benched)
    VALUES (@ID_Equipa, @ID_Jogador, @BenchedStatus);

    -- Atualizar orçamento
    UPDATE FantasyChamp.Equipa
    SET Orçamento = Orçamento - @Preco
    WHERE ID = @ID_Equipa;

    SET @Resultado = 1;
    SET @Mensagem = CASE WHEN @BenchedStatus = 1
                        THEN 'Player added to bench'
                        ELSE 'Player added to field' END;

    COMMIT TRANSACTION;
END;

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

    -- 4. Calcular pontuação acumulada (soma de todas as jornadas até esta)
    DECLARE @PontuacaoAcumulada INT;
    DECLARE @NumeroJornadaAtual INT;

    -- Obter o número da jornada atual
    SELECT @NumeroJornadaAtual = Numero 
    FROM FantasyChamp.Jornada 
    WHERE ID = @ID_Jornada;

    -- Somar pontos de todas as jornadas até à atual (inclusive)
    SELECT @PontuacaoAcumulada = ISNULL(SUM(PE.pontuação_jornada), 0)
    FROM FantasyChamp.Pontuação_Equipa PE
    INNER JOIN FantasyChamp.Jornada J ON PE.ID_jornada = J.ID
    WHERE PE.ID_Equipa = @ID_Equipa 
      AND J.Numero <= @NumeroJornadaAtual;

    -- Adicionar a pontuação da jornada atual (que ainda pode não estar na tabela)
    SET @PontuacaoAcumulada = ISNULL(@PontuacaoAcumulada, 0) + @PontuacaoJornada;

    -- 5. Atualizar tabela Pontuação_Equipa
    IF EXISTS (SELECT 1 FROM FantasyChamp.Pontuação_Equipa
               WHERE ID_Equipa = @ID_Equipa AND ID_jornada = @ID_Jornada)
    BEGIN
        -- Atualizar
        UPDATE FantasyChamp.Pontuação_Equipa
        SET pontuação_jornada = @PontuacaoJornada,
            pontuação_acumulada = @PontuacaoAcumulada
        WHERE ID_Equipa = @ID_Equipa AND ID_jornada = @ID_Jornada;
    END
    ELSE
    BEGIN
        -- Inserir
        INSERT INTO FantasyChamp.Pontuação_Equipa
            (ID_Equipa, ID_jornada, pontuação_jornada, pontuação_acumulada)
        VALUES
            (@ID_Equipa, @ID_Jornada, @PontuacaoJornada, @PontuacaoAcumulada);
    END

    SET @Resultado = 1;
    SET @Mensagem = 'Pontuation updated successfully: ' + CAST(@PontuacaoJornada AS NVARCHAR(10)) + ' (Accumulated: ' + CAST(@PontuacaoAcumulada AS NVARCHAR(10)) + ')';
END;

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

CREATE PROCEDURE FantasyChamp.CalcularPontuacaoEquipa
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16),
    @PontuacaoTotal INT OUTPUT,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Resultado = 0;
    SET @Mensagem = '';
    SET @PontuacaoTotal = 0;

    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Equipa WHERE ID = @ID_Equipa)
    BEGIN
        SET @Mensagem = 'Team not found';
        RETURN;
    END

    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = @ID_Jornada)
    BEGIN
        SET @Mensagem = 'Round not found';
        RETURN;
    END

    SELECT @PontuacaoTotal = SUM(CAST(PJ.pontuação_total AS INT))
    FROM FantasyChamp.Pertence PE
    JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
    LEFT JOIN FantasyChamp.Pontuação_Jogador PJ
        ON J.ID = PJ.ID_jogador AND PJ.ID_jornada = @ID_Jornada
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 0
      AND ISNUMERIC(PJ.pontuação_total) = 1;

    SET @PontuacaoTotal = ISNULL(@PontuacaoTotal, 0);

    SET @Resultado = 1;
    SET @Mensagem = 'Pontuation calculated successfully: ' + CAST(@PontuacaoTotal AS NVARCHAR(10));
END;

ALTER PROCEDURE FantasyChamp.CalcularPontuacaoJogador
    @ID_Jogador VARCHAR(16),
    @ID_Jornada VARCHAR(16),
    @Pontuacao INT OUTPUT,
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    SET @Resultado = 0;
    SET @Mensagem = '';
    SET @Pontuacao = 0;

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

    -- Obter estatísticas do jogador nesta jornada
    DECLARE @GolosMarcados INT, @Assistencias INT,
            @CartoesAmarelos INT, @CartoesVermelhos INT,
            @TempoJogo INT, @GolosSofridos INT;
    DECLARE @Posicao NVARCHAR(50);

    -- Obter posição do jogador
    SELECT @Posicao = P.Posição
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE J.ID = @ID_Jogador;

    SELECT
        @GolosMarcados = ISNULL(GolosMarcados, 0),
        @Assistencias = ISNULL(Assistencias, 0),
        @CartoesAmarelos = ISNULL(CartoesAmarelos, 0),
        @CartoesVermelhos = ISNULL(CartoesVermelhos, 0),
        @TempoJogo = ISNULL(TempoJogo, 0),
        @GolosSofridos = ISNULL(GolosSofridos, 0)
    FROM FantasyChamp.Pontuação_Jogador
    WHERE ID_jogador = @ID_Jogador AND ID_jornada = @ID_Jornada;

    IF @GolosMarcados IS NULL
    BEGIN
        SET @Pontuacao = 0;
        SET @Resultado = 1;
        SET @Mensagem = 'Player has no statistics for this round';
        RETURN;
    END

    SET @Pontuacao =
        (@GolosMarcados * 5) +
        (@Assistencias * 3) -
        (@CartoesAmarelos * 1) -
        (@CartoesVermelhos * 3);

    -- Pontos por tempo jogado (1 ponto por cada 30 minutos)
    IF @TempoJogo >= 30
        SET @Pontuacao = @Pontuacao + (@TempoJogo / 30);

    -- Bónus/Penalizações específicas para Goalkeeper e Defender
    IF @Posicao IN ('Goalkeeper', 'Defender')
    BEGIN
        -- Bónus por clean sheet (0 golos sofridos e jogou 60+ minutos)
        IF @GolosSofridos = 0 AND @TempoJogo >= 60
            SET @Pontuacao = @Pontuacao + 4;
        
        -- Penalização por golos sofridos
        IF @GolosSofridos > 0
            SET @Pontuacao = @Pontuacao - @GolosSofridos;
    END

    -- Garantir que a pontuação não seja negativa
    IF @Pontuacao < 0
        SET @Pontuacao = 0;

    SET @Resultado = 1;
    SET @Mensagem = 'Pontuation calculated successfully';
END;

CREATE PROCEDURE FantasyChamp.sp_CriarEquipa
    @Nome NVARCHAR(100),
    @ID_Utilizador NVARCHAR(100),
    @EquipaID UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Gerar novo ID
        SET @EquipaID = NEWID();

        -- Inserir equipa
        INSERT INTO FantasyChamp.Equipa (ID, Nome, Orçamento, PontuaçãoTotal, ID_Utilizador)
        VALUES (@EquipaID, @Nome, 100.00, 0, @ID_Utilizador);

        -- Log ou ações adicionais podem ser adicionadas aqui

        COMMIT TRANSACTION;

        -- Retorna sucesso
        RETURN 0;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        -- Relançar erro para a aplicação
        THROW;

        RETURN -1;
    END CATCH
END;

CREATE PROCEDURE FantasyChamp.CriarLiga
    @Nome NVARCHAR(100),
    @Data_Inicio DATE,
    @Data_Fim DATE,
    @ID_tipoLiga VARCHAR(16) = 'LT02',
    @ID_criador UNIQUEIDENTIFIER = NULL,
    @Codigo_Convite VARCHAR(10) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @LigaID UNIQUEIDENTIFIER = NEWID();
    DECLARE @Codigo VARCHAR(10);

    -- Gerar código se não fornecido
    IF @Codigo_Convite IS NULL OR LTRIM(RTRIM(@Codigo_Convite)) = ''
    BEGIN
        SET @Codigo = LEFT(CAST(NEWID() AS NVARCHAR(36)), 6);
    END
    ELSE
    BEGIN
        SET @Codigo = @Codigo_Convite;
    END

    BEGIN TRANSACTION;

    -- Inserir liga
    INSERT INTO FantasyChamp.Liga
        (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
    VALUES
        (@LigaID, @Nome, @Data_Inicio, @Data_Fim, @ID_tipoLiga, @ID_criador, UPPER(@Codigo));

    -- Adicionar criador
    IF @ID_criador IS NOT NULL
    BEGIN
        INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
        VALUES (@ID_criador, @LigaID);
    END

    COMMIT TRANSACTION;

    -- Retornar resultado
    SELECT
        @LigaID as ID,
        @Codigo as Codigo_Convite,
        1 as Sucesso;
END;

CREATE PROCEDURE FantasyChamp.CriarLigaPublica
    @Nome NVARCHAR(100),
    @ID_criador UNIQUEIDENTIFIER = NULL,
    @LigaID UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    -- Gerar ID (igual ao Python)
    SET @LigaID = NEWID();

    -- Inserir liga (igual ao Python)
    INSERT INTO FantasyChamp.Liga
        (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
    VALUES
        (@LigaID, @Nome, GETDATE(), '2026-05-30', 'LT01', @ID_criador, NULL);

    -- Adicionar criador (se existir) - igual ao Python
    IF @ID_criador IS NOT NULL
    BEGIN
        INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
        VALUES (@ID_criador, @LigaID);
    END
END;

CREATE PROCEDURE sp_CriarLigaPaisSeNaoExistir
    @Pais NVARCHAR(100),
    @CriadorID UNIQUEIDENTIFIER,
    @LigaID UNIQUEIDENTIFIER OUTPUT,
    @Sucesso BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @LigaTipoPublica VARCHAR(16) = 'LT01';
    DECLARE @CodigoPais VARCHAR(16);

    BEGIN TRY
        -- Verificar se o país existe
        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Pais WHERE Pais.nome = @Pais OR ID = @Pais)
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Country not found';
            RETURN;
        END

        -- Verificar se já existe liga do país
        SELECT @LigaID = ID
        FROM FantasyChamp.Liga
        WHERE Nome = @Pais AND ID_tipoLiga = @LigaTipoPublica;

        -- Se não existe, criar
        IF @LigaID IS NULL
        BEGIN
            SET @LigaID = NEWID();

            INSERT INTO FantasyChamp.Liga
                (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
            VALUES
                (@LigaID, @Pais, GETDATE(),
                CONVERT(DATE, '2026-05-30', 23),
                @LigaTipoPublica, '00000000-0000-0000-0000-000000000000', null);

            SET @Sucesso = 1;
            SET @Mensagem = 'League created successfully';
        END
        ELSE
        BEGIN
            SET @Sucesso = 1;
            SET @Mensagem = 'League already exists';
        END

    END TRY
    BEGIN CATCH
        SET @Sucesso = 0;
        SET @Mensagem = 'Erro: ' + ERROR_MESSAGE();
        SET @LigaID = NULL;
    END CATCH
END;

CREATE OR ALTER PROCEDURE FantasyChamp.sp_CriarUtilizadorComLigas
    @PrimeiroNome NVARCHAR(100),
    @Apelido NVARCHAR(100),
    @Email NVARCHAR(255),
    @Senha NVARCHAR(255),
    @Pais NVARCHAR(100),
    @Nacionalidade NVARCHAR(100),
    @DataNascimento DATE,
    @UserID UNIQUEIDENTIFIER OUTPUT,
    @Sucesso BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    -- Inicializar outputs
    SET @UserID = NULL;
    SET @Sucesso = 0;
    SET @Mensagem = '';

    -- VALIDAÇÕES ANTES DE ABRIR TRANSAÇÃO
    -- Verificar email duplicado
    IF EXISTS (SELECT 1 FROM FantasyChamp.Utilizador WHERE Email = @Email)
    BEGIN
        SET @Mensagem = 'Email already exists';
        RETURN;
    END

    -- Verificar se a senha foi fornecida e não está vazia
    IF @Senha IS NULL OR LTRIM(RTRIM(@Senha)) = ''
    BEGIN
        SET @Mensagem = 'Password is required';
        RETURN;
    END

    -- Verificar se o país existe na tabela de países
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Pais WHERE nome = @Pais OR ID = @Pais)
    BEGIN
        SET @Mensagem = 'Invalid Country';
        RETURN;
    END

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Criar utilizador
        SET @UserID = NEWID();
        INSERT INTO FantasyChamp.Utilizador
            (ID, PrimeiroNome, Apelido, Email, Senha, País, Nacionalidade, DataDeNascimento)
        VALUES
            (@UserID, @PrimeiroNome, @Apelido, @Email, @Senha, @Pais, @Nacionalidade, @DataNascimento);

        SET @Sucesso = 1;
        SET @Mensagem = 'Account created successfully';

        COMMIT TRANSACTION;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @Sucesso = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();
        SET @UserID = NULL;
    END CATCH
END;
GO

CREATE PROCEDURE sp_EquipaJornada
    @UserID UNIQUEIDENTIFIER,
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jornada VARCHAR(16),
    @Resultado BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @PontuacaoTotal INT;
    DECLARE @EquipaExiste BIT = 0;

    BEGIN TRY
        -- Verificar se o utilizador tem permissão para ver esta equipa
        SELECT @EquipaExiste = 1
        FROM FantasyChamp.Equipa E
        WHERE E.ID = @ID_Equipa
          AND E.ID_utilizador = @UserID;

        IF @EquipaExiste = 0
        BEGIN
            SET @Resultado = 0;
            SET @Mensagem = 'You do not have permission to view this team';
            RETURN;
        END

        -- Verificar se a jornada existe
        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jornada WHERE ID = @ID_Jornada)
        BEGIN
            SET @Resultado = 0;
            SET @Mensagem = 'Round not found';
            RETURN;
        END

        -- Obter detalhes da equipa com pontuações
        EXEC sp_ObterEquipaComPontuacoes
            @ID_Equipa = @ID_Equipa,
            @ID_Jornada = @ID_Jornada,
            @PontuacaoTotal = @PontuacaoTotal OUTPUT,
            @Resultado = @Resultado OUTPUT,
            @Mensagem = @Mensagem OUTPUT;

        IF @Resultado = 0
            RETURN;

        -- Retornar também informações da jornada
        SELECT
            J.ID AS JornadaID,
            J.Numero AS JornadaNumero,
            J.Data_Inicio,
            J.Data_Fim,
            @PontuacaoTotal AS PontuacaoTotalEquipa
        FROM FantasyChamp.Jornada J
        WHERE J.ID = @ID_Jornada;

        SET @Resultado = 1;
        SET @Mensagem = 'Operation completed successfully';

    END TRY
    BEGIN CATCH
        SET @Resultado = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();
    END CATCH
END;

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

CREATE PROCEDURE FantasyChamp.JuntarLiga
    @ID_Utilizador UNIQUEIDENTIFIER,
    @ID_Liga UNIQUEIDENTIFIER,
    @Codigo VARCHAR(10) = NULL,
    @Resultado BIT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @TipoLiga VARCHAR(16);
    DECLARE @CodigoLiga VARCHAR(10);

    SET @Resultado = 0;

    -- Verificar se já está na liga
    IF EXISTS (SELECT 1 FROM FantasyChamp.Participa
               WHERE ID_Utilizador = @ID_Utilizador AND ID_Liga = @ID_Liga)
    BEGIN
        RETURN;
    END

    -- Obter informações da liga
    SELECT @TipoLiga = ID_tipoLiga, @CodigoLiga = Código_Convite
    FROM FantasyChamp.Liga
    WHERE ID = @ID_Liga;

    IF @TipoLiga IS NULL
    BEGIN
        RETURN;
    END

    -- Verificar se é privada e código está correto
    IF @TipoLiga = 'LT02'  -- privada
    BEGIN
        IF @Codigo IS NULL OR @Codigo != @CodigoLiga
        BEGIN
            RETURN;  -- Código inválido, @Resultado = 0
        END
    END

    -- Inserir
    INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
    VALUES (@ID_Utilizador, @ID_Liga);

    SET @Resultado = 1;  -- Sucesso
END;

CREATE PROCEDURE FantasyChamp.JuntarLigaAutomatico
    @ID_Utilizador UNIQUEIDENTIFIER,
    @ID_Liga UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    -- Verificar se já está na liga
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Participa
                   WHERE ID_Utilizador = @ID_Utilizador AND ID_Liga = @ID_Liga)
    BEGIN
        -- Inserir
        INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
        VALUES (@ID_Utilizador, @ID_Liga);
    END
END;

CREATE PROCEDURE FantasyChamp.ObterDetalhesEquipaParaVisualizacao
    @ID_Equipa UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    -- Informações básicas da equipa
    SELECT
        e.ID,
        e.Nome,
        e.Orçamento,
        e.PontuaçãoTotal,
        e.ID_Utilizador,
        CONCAT(u.PrimeiroNome, ' ', u.Apelido) AS Nome_Utilizador,
        -- Estatísticas calculadas
        (SELECT COUNT(*) FROM FantasyChamp.Pertence WHERE ID_Equipa = @ID_Equipa) AS Total_Jogadores,
        (SELECT COUNT(*) FROM FantasyChamp.Pertence WHERE ID_Equipa = @ID_Equipa AND benched = 0) AS Total_Titulares
    FROM FantasyChamp.Equipa e
    LEFT JOIN FantasyChamp.Utilizador u ON e.ID_Utilizador = u.ID
    WHERE e.ID = @ID_Equipa;

    -- Guarda-Redes
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Goalkeeper'
    ORDER BY p.benched, j.Nome;

    -- Defesas
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Defender'
    ORDER BY p.benched, j.Nome;

    -- Médios
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Midfielder'
    ORDER BY p.benched, j.Nome;

    -- Avançados
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Forward'
    ORDER BY p.benched, j.Nome;

    -- Estatísticas
    SELECT
        -- Contagem por posição
        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Goalkeeper') AS Total_GR,

        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Defender') AS Total_Defesas,

        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Midfielder') AS Total_Medios,

        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Forward') AS Total_Avancados,

        -- Valor total
        (SELECT SUM(j.Preço) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa) AS Valor_Total_Plantel

END;

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

CREATE PROCEDURE FantasyChamp.ObterJornadaAtual
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @JornadaID VARCHAR(16);
    DECLARE @Numero INT;

    SELECT TOP 1
        @JornadaID = ID,
        @Numero = Numero
    FROM FantasyChamp.Jornada
    WHERE GETDATE() BETWEEN Data_Inicio AND Data_Fim
    ORDER BY Numero;

    IF @JornadaID IS NULL
    BEGIN
        SELECT TOP 1
            @JornadaID = ID,
            @Numero = Numero
        FROM FantasyChamp.Jornada
        ORDER BY Numero DESC;
    END

    SELECT
        @JornadaID as ID,
        @Numero as Numero;
END;

CREATE PROCEDURE FantasyChamp.ObterLigasPublicasParaUtilizador
    @PaisUser NVARCHAR(50),
    @ID_User UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        L.ID,
        L.Nome,
        L.Data_Inicio,
        L.Data_Fim,
        L.ID_tipoLiga,
        L.ID_criador,
        L.Código_Convite,
        U.PrimeiroNome
    FROM FantasyChamp.Liga L
    JOIN FantasyChamp.Utilizador U ON L.ID_criador = U.ID
    WHERE
        L.ID_tipoLiga = 'LT01'
        AND L.Data_Fim > GETDATE()
        AND L.Nome IN ('Mundial', @PaisUser)
        AND L.ID NOT IN (
            SELECT ID_Liga FROM FantasyChamp.Participa
            WHERE ID_Utilizador = @ID_User
        )
    ORDER BY L.Nome;
END;

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
            -- Ranking geral - usar CTE para calcular totais primeiro
            ;WITH EquipaPontuacoes AS (
                SELECT
                    E.ID AS id_equipa,
                    E.Nome AS nome_equipa,
                    E.ID_utilizador AS id_utilizador,
                    U.PrimeiroNome + ' ' + U.Apelido AS nome_utilizador,
                    ISNULL(MAX(PE.pontuação_acumulada), 0) AS pontuacao_total
                FROM FantasyChamp.Participa P
                JOIN FantasyChamp.Utilizador U ON P.ID_Utilizador = U.ID
                INNER JOIN FantasyChamp.Equipa E ON U.ID = E.ID_utilizador
                LEFT JOIN FantasyChamp.Pontuação_Equipa PE ON E.ID = PE.ID_equipa
                WHERE P.ID_Liga = @ID_Liga
                GROUP BY E.ID, E.Nome, E.ID_utilizador, U.PrimeiroNome, U.Apelido
            )
            SELECT
                ROW_NUMBER() OVER (ORDER BY pontuacao_total DESC, nome_utilizador) AS posicao,
                nome_utilizador,
                nome_equipa,
                pontuacao_total AS pontuacao_acumulada,
                id_equipa,
                id_utilizador,
                pontuacao_total AS pontuacao
            FROM EquipaPontuacoes
            ORDER BY pontuacao_total DESC, nome_utilizador;
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

ALTER PROCEDURE FantasyChamp.RemoverJogadorEquipa
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jogador varchar(16)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Preco_Jogador DECIMAL(10,2);

    BEGIN TRANSACTION;

    -- Obter preço do jogador
    SELECT @Preco_Jogador = J.Preço
    FROM FantasyChamp.Jogador J
    INNER JOIN FantasyChamp.Pertence P ON J.ID = P.ID_Jogador
    WHERE P.ID_Equipa = @ID_Equipa
      AND P.ID_Jogador = @ID_Jogador;

    -- Se encontrou jogador na equipa
    IF @Preco_Jogador IS NOT NULL
    BEGIN
        -- Remover da equipa
        DELETE FROM FantasyChamp.Pertence
        WHERE ID_Equipa = @ID_Equipa
          AND ID_Jogador = @ID_Jogador;

        -- Devolver dinheiro
        UPDATE FantasyChamp.Equipa
        SET Orçamento = Orçamento + @Preco_Jogador
        WHERE ID = @ID_Equipa;
    END

    COMMIT TRANSACTION;
END;

CREATE PROCEDURE sp_TrocarJogadorBancoCampo
    @ID_Equipa UNIQUEIDENTIFIER,
    @ID_Jogador_Banco VARCHAR(16),
    @ID_Jogador_Campo VARCHAR(16),
    @Sucesso BIT OUTPUT,
    @Mensagem NVARCHAR(200) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Benched_Banco BIT, @Benched_Campo BIT;
    DECLARE @Posicao_Banco NVARCHAR(50), @Posicao_Campo NVARCHAR(50);
    DECLARE @Count_GR_Banco INT, @Count_GR_Campo INT;

    BEGIN TRY
        -- 1. Verificar se os jogadores existem na BD
        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jogador WHERE ID = @ID_Jogador_Banco)
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Player from bench not found';
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jogador WHERE ID = @ID_Jogador_Campo)
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Player from field not found';
            RETURN;
        END

        -- 2. Verificar status dos jogadores (benched)
        SELECT @Benched_Banco = benched
        FROM FantasyChamp.Pertence
        WHERE ID_Equipa = @ID_Equipa AND ID_Jogador = @ID_Jogador_Banco;

        SELECT @Benched_Campo = benched
        FROM FantasyChamp.Pertence
        WHERE ID_Equipa = @ID_Equipa AND ID_Jogador = @ID_Jogador_Campo;

        -- Verificar se pertencem à equipa
        IF @Benched_Banco IS NULL
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Player from bench does not belong to this team';
            RETURN;
        END

        IF @Benched_Campo IS NULL
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Player from field does not belong to this team';
            RETURN;
        END

        -- Verificar se estão nas posições corretas
        IF @Benched_Banco != 1 OR @Benched_Campo != 0
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Players are not in the correct positions (bench/field)';
            RETURN;
        END

        -- 3. Obter posições dos jogadores
        SELECT @Posicao_Banco = P.Posição
        FROM FantasyChamp.Jogador J
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        WHERE J.ID = @ID_Jogador_Banco;

        SELECT @Posicao_Campo = P.Posição
        FROM FantasyChamp.Jogador J
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        WHERE J.ID = @ID_Jogador_Campo;

        -- NOVA LÓGICA: Permitir trocas entre TODAS as posições, EXCETO:
        -- 1. GR só pode trocar com GR
        -- 2. Outras posições NÃO podem trocar com GR
        
        -- Verificar se um é GR e outro não é
        IF (@Posicao_Banco = 'Goalkeeper' AND @Posicao_Campo != 'Goalkeeper') OR
           (@Posicao_Banco != 'Goalkeeper' AND @Posicao_Campo = 'Goalkeeper')
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Goalkeepers can only swap with other goalkeepers. Other positions cannot swap with goalkeepers.';
            RETURN;
        END

        -- 4. VALIDAÇÕES ESPECIAIS APENAS PARA GOALKEEPERS
        --    (Para outras posições, a troca é sempre válida mesmo entre posições diferentes)

        IF @Posicao_Campo = 'Goalkeeper'
        BEGIN
            -- Contar GRs no banco (ANTES da troca)
            SELECT @Count_GR_Banco = COUNT(*)
            FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE PE.ID_Equipa = @ID_Equipa
              AND PE.benched = 1
              AND P.Posição = 'Goalkeeper';

            -- Contar GRs em campo (ANTES da troca)
            SELECT @Count_GR_Campo = COUNT(*)
            FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE PE.ID_Equipa = @ID_Equipa
              AND PE.benched = 0
              AND P.Posição = 'Goalkeeper';

            -- VALIDAÇÃO: Deve haver pelo menos 1 GR no banco E 1 GR em campo
            -- Como é uma TROCA de GRs, só falharia se houvesse apenas 1 GR total
            IF @Count_GR_Banco = 0 OR @Count_GR_Campo = 0
            BEGIN
                SET @Sucesso = 0;
                SET @Mensagem = 'There must be at least 1 goalkeeper on the bench and 1 on the field';
                RETURN;
            END

            -- Se há pelo menos 1 GR em cada lado, a troca é válida
            -- (mantém 1 em campo e 1 no banco, apenas trocam de lugar)
        END

        -- 5. VALIDAÇÃO DE NÚMEROS MÍNIMOS POR POSIÇÃO NA EQUIPA TITULAR
        --    Garantir que após a troca existem:
        --    - Pelo menos 3 Defesas
        --    - Pelo menos 2 Médios
        --    - Pelo menos 1 Avançado
        
        -- Apenas validar se NÃO for troca entre GRs (já validado acima)
        IF @Posicao_Campo != 'Goalkeeper'
        BEGIN
            DECLARE @Count_Defenders_Campo INT, @Count_Midfielders_Campo INT, @Count_Forwards_Campo INT;
            DECLARE @Count_After_Defenders INT, @Count_After_Midfielders INT, @Count_After_Forwards INT;
            
            -- Contar jogadores em campo POR POSIÇÃO (ANTES da troca)
            SELECT @Count_Defenders_Campo = COUNT(*)
            FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE PE.ID_Equipa = @ID_Equipa
              AND PE.benched = 0
              AND P.Posição = 'Defender';
            
            SELECT @Count_Midfielders_Campo = COUNT(*)
            FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE PE.ID_Equipa = @ID_Equipa
              AND PE.benched = 0
              AND P.Posição = 'Midfielder';
            
            SELECT @Count_Forwards_Campo = COUNT(*)
            FROM FantasyChamp.Pertence PE
            JOIN FantasyChamp.Jogador J ON PE.ID_Jogador = J.ID
            JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
            WHERE PE.ID_Equipa = @ID_Equipa
              AND PE.benched = 0
              AND P.Posição = 'Forward';
            
            -- Simular contagens DEPOIS da troca
            SET @Count_After_Defenders = @Count_Defenders_Campo;
            SET @Count_After_Midfielders = @Count_Midfielders_Campo;
            SET @Count_After_Forwards = @Count_Forwards_Campo;
            
            -- Jogador do banco vai para campo (adiciona)
            IF @Posicao_Banco = 'Defender'
                SET @Count_After_Defenders = @Count_After_Defenders + 1;
            ELSE IF @Posicao_Banco = 'Midfielder'
                SET @Count_After_Midfielders = @Count_After_Midfielders + 1;
            ELSE IF @Posicao_Banco = 'Forward'
                SET @Count_After_Forwards = @Count_After_Forwards + 1;
            
            -- Jogador do campo vai para banco (remove)
            IF @Posicao_Campo = 'Defender'
                SET @Count_After_Defenders = @Count_After_Defenders - 1;
            ELSE IF @Posicao_Campo = 'Midfielder'
                SET @Count_After_Midfielders = @Count_After_Midfielders - 1;
            ELSE IF @Posicao_Campo = 'Forward'
                SET @Count_After_Forwards = @Count_After_Forwards - 1;
            
            -- VALIDAR NÚMEROS MÍNIMOS
            IF @Count_After_Defenders < 3
            BEGIN
                SET @Sucesso = 0;
                SET @Mensagem = 'Team need at least 3 defenders';
                RETURN;
            END
            
            IF @Count_After_Midfielders < 2
            BEGIN
                SET @Sucesso = 0;
                SET @Mensagem = 'Team need at least 2 midfielders';
                RETURN;
            END
            
            IF @Count_After_Forwards < 1
            BEGIN
                SET @Sucesso = 0;
                SET @Mensagem = 'Team need at least 1 forward';
                RETURN;
            END
        END

        -- 6. Fazer a troca (transação atômica)
        BEGIN TRANSACTION;

        -- Jogador do banco vai para campo
        UPDATE FantasyChamp.Pertence
        SET benched = 0
        WHERE ID_Equipa = @ID_Equipa AND ID_Jogador = @ID_Jogador_Banco;

        -- Jogador do campo vai para banco
        UPDATE FantasyChamp.Pertence
        SET benched = 1
        WHERE ID_Equipa = @ID_Equipa AND ID_Jogador = @ID_Jogador_Campo;

        COMMIT TRANSACTION;

        SET @Sucesso = 1;
        SET @Mensagem = 'Swap completed successfully!';

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @Sucesso = 0;
        SET @Mensagem = 'Error: ' + ERROR_MESSAGE();
    END CATCH
END;
GO

-----------------------------
-- UDFS
----------------------------

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

CREATE FUNCTION FantasyChamp.ContarJogadoresPorPosicao
(
    @ID_Equipa UNIQUEIDENTIFIER,
    @Apenas_Campo BIT = 0,
    @Apenas_Banco BIT = 0
)
RETURNS @Result TABLE
(
    Posicao VARCHAR(50),
    Contagem INT
)
AS
BEGIN
    INSERT INTO @Result
    SELECT
        P.Posição,
        COUNT(*) as Contagem
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
    WHERE PE.ID_Equipa = @ID_Equipa
      AND (@Apenas_Campo = 0 OR PE.benched = 0)
      AND (@Apenas_Banco = 0 OR PE.benched = 1)
    GROUP BY P.Posição

    RETURN
END

CREATE FUNCTION FantasyChamp.ObterJogadoresBancoPorPosicao
(
    @ID_Equipa UNIQUEIDENTIFIER,
    @Posicao VARCHAR(50)
)
RETURNS TABLE
AS
RETURN
    SELECT
        J.ID,
        J.Nome,
        J.Preço,
        J.jogador_imagem,
        E.Estado
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
    WHERE PE.ID_Equipa = @ID_Equipa
      AND PE.benched = 1
      AND P.Posição = @Posicao;

CREATE FUNCTION FantasyChamp.fn_ObterPosicaoJogador
    (@ID_Jogador UNIQUEIDENTIFIER)
RETURNS VARCHAR(50)
AS
BEGIN
    DECLARE @Posicao VARCHAR(50);

    SELECT @Posicao = P.Posição
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    WHERE J.ID = @ID_Jogador;

    RETURN @Posicao;
END;

CREATE FUNCTION FantasyChamp.fn_OrcamentoSuficiente
(
    @ID_Equipa UNIQUEIDENTIFIER,
    @Preco_Jogador DECIMAL(10,2)
)
RETURNS BIT
AS
BEGIN
    DECLARE @Orcamento DECIMAL(10,2);

    SELECT @Orcamento = ISNULL(Orçamento, 0)
    FROM FantasyChamp.Equipa
    WHERE ID = @ID_Equipa;

    RETURN CASE WHEN @Orcamento >= @Preco_Jogador THEN 1 ELSE 0 END;
END;