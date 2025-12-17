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