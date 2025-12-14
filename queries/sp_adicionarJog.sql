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
        SET @Mensagem = 'Jogador já está na equipa';
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
        SET @Mensagem = 'Jogador não encontrado';
        ROLLBACK TRANSACTION;
        RETURN;
    END

    -- Verificar orçamento
    SELECT @Orcamento = Orçamento FROM FantasyChamp.Equipa WHERE ID = @ID_Equipa;

    IF @Orcamento < @Preco
    BEGIN
        SET @Resultado = 0;
        SET @Mensagem = 'Orçamento insuficiente';
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
    SET @BenchedStatus = 1; -- Default: vai para banco

    -- REGRA 1: GR sem GR no banco vai para banco
    IF @Posicao = 'Goalkeeper' AND @ContadorGR_Banco = 0
        SET @BenchedStatus = 1;
    -- REGRA 2: GR com GR no banco vai para campo
    ELSE IF @Posicao = 'Goalkeeper' AND @ContadorGR_Banco >= 1
        SET @BenchedStatus = 0;
    -- REGRA 3: Banco cheio (4 jogadores) vai para campo
    ELSE IF @TotalBanco >= 4
        SET @BenchedStatus = 0;
    -- REGRA 4: Se tem 3 no banco mas não tem GR, este vai para campo
    -- (para deixar espaço para o GR obrigatório)
    ELSE IF @TotalBanco = 3 AND @ContadorGR_Banco = 0 AND @Posicao != 'Goalkeeper'
        SET @BenchedStatus = 0;
    -- REGRA 5: Para avançados - se já tem 2 avançados no banco, este vai para campo
    ELSE IF @Posicao = 'Forward' AND @ContadorAvancados_Banco >= 2
        SET @BenchedStatus = 0;
    -- REGRA 6: Se ainda tem espaço no banco (menos de 3) e já tem GR no banco
    ELSE IF @TotalBanco < 3 AND @ContadorGR_Banco >= 1
    BEGIN
        -- Verifica se ao adicionar este jogador ao banco, ainda sobra pelo menos 1 avançado para o campo
        IF @Posicao = 'Forward'
        BEGIN
            SET @TotalAvancados = @ContadorAvancados_Banco + @ContadorAvancados_Campo;
            -- Se já tem 2 no banco e este é o 3º avançado, vai para o campo
            IF @TotalAvancados >= 2 AND @ContadorAvancados_Banco >= 2
                SET @BenchedStatus = 0;
            ELSE
                SET @BenchedStatus = 1;
        END
        ELSE
            SET @BenchedStatus = 1;
    END
    -- REGRA 7: Se tem menos de 4 no banco, tem GR, e não quebra outras regras
    ELSE IF @TotalBanco < 4 AND @ContadorGR_Banco >= 1
    BEGIN
        IF @Posicao = 'Forward'
        BEGIN
            -- Máximo 2 avançados no banco
            IF @ContadorAvancados_Banco >= 2
                SET @BenchedStatus = 0;
            ELSE
                SET @BenchedStatus = 1;
        END
        ELSE
            SET @BenchedStatus = 1;
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
                        THEN 'Jogador adicionado ao banco'
                        ELSE 'Jogador adicionado ao campo' END;

    COMMIT TRANSACTION;
END;