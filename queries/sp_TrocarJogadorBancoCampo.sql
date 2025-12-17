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