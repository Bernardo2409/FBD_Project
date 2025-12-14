CREATE OR ALTER PROCEDURE sp_TrocarJogadorBancoCampo
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
            SET @Mensagem = 'Jogador do banco não encontrado';
            RETURN;
        END

        IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Jogador WHERE ID = @ID_Jogador_Campo)
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Jogador do campo não encontrado';
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
            SET @Mensagem = 'Jogador do banco não pertence a esta equipa';
            RETURN;
        END

        IF @Benched_Campo IS NULL
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Jogador do campo não pertence a esta equipa';
            RETURN;
        END

        -- Verificar se estão nas posições corretas
        IF @Benched_Banco != 1 OR @Benched_Campo != 0
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Jogadores não estão nas posições corretas (banco/campo)';
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

        -- Verificar se são da mesma posição
        IF @Posicao_Banco != @Posicao_Campo
        BEGIN
            SET @Sucesso = 0;
            SET @Mensagem = 'Jogadores devem ser da mesma posição para trocar. ' +
                           @Posicao_Banco + ' ≠ ' + @Posicao_Campo;
            RETURN;
        END

        -- 4. VALIDAÇÕES ESPECIAIS APENAS PARA GOALKEEPERS
        --    (Para outras posições, a troca é sempre válida pois mantém o total)

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
                SET @Mensagem = 'Deve haver pelo menos 1 guarda-redes no banco e 1 em campo';
                RETURN;
            END

            -- Se há pelo menos 1 GR em cada lado, a troca é válida
            -- (mantém 1 em campo e 1 no banco, apenas trocam de lugar)
        END

        -- 5. Para TODAS AS OUTRAS POSIÇÕES (Defender, Midfielder, Forward):
        --    Como é uma TROCA da mesma posição, o total em campo NÃO MUDA!
        --    Portanto, se tinha 1+ Forward em campo antes, terá 1+ depois.
        --    NÃO É NECESSÁRIA validação adicional!

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
        SET @Mensagem = 'Troca realizada com sucesso!';

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @Sucesso = 0;
        SET @Mensagem = 'Erro: ' + ERROR_MESSAGE();
    END CATCH
END;
GO