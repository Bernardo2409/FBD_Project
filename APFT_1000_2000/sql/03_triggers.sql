
-- 1 TRIGGER: Criar ligas Mundial e do País ao criar utilizador

CREATE TRIGGER FantasyChamp.trg_Utilizador_CriarLigasPais
ON FantasyChamp.Utilizador
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @UserID UNIQUEIDENTIFIER;
    DECLARE @Pais NVARCHAR(50);
    DECLARE @LigaMundialID UNIQUEIDENTIFIER;
    DECLARE @LigaPaisID UNIQUEIDENTIFIER;
    DECLARE @LigaTipoPublica VARCHAR(16) = 'LT01';
    DECLARE @CriadorPadrao UNIQUEIDENTIFIER = '00000000-0000-0000-0000-000000000000';
    
    BEGIN TRY

        DECLARE user_cursor CURSOR FOR
            SELECT ID, País
            FROM inserted
            WHERE País IS NOT NULL AND LTRIM(RTRIM(País)) != '';
        
        OPEN user_cursor;
        FETCH NEXT FROM user_cursor INTO @UserID, @Pais;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- 1) LIGA MUNDIAL
            -- Verificar se já existe liga Mundial
            SELECT @LigaMundialID = ID
            FROM FantasyChamp.Liga
            WHERE Nome = 'Mundial' AND ID_tipoLiga = @LigaTipoPublica;
            
            -- Se não existe, criar
            IF @LigaMundialID IS NULL
            BEGIN
                SET @LigaMundialID = NEWID();
                INSERT INTO FantasyChamp.Liga
                    (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
                VALUES
                    (@LigaMundialID, 'Mundial', GETDATE(), '2026-05-30', 
                     @LigaTipoPublica, @CriadorPadrao, NULL);
            END
            
            -- Adicionar utilizador à Liga Mundial (se ainda não estiver)
            IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Participa
                          WHERE ID_Utilizador = @UserID AND ID_Liga = @LigaMundialID)
            BEGIN
                INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
                VALUES (@UserID, @LigaMundialID);
            END
            
            -- 2) LIGA DO PAÍS
            -- Verificar se o país existe na tabela de países
            IF EXISTS (SELECT 1 FROM FantasyChamp.Pais 
                      WHERE nome = @Pais OR ID = @Pais)
            BEGIN
                -- Verificar se já existe liga do país
                SELECT @LigaPaisID = ID
                FROM FantasyChamp.Liga
                WHERE Nome = @Pais AND ID_tipoLiga = @LigaTipoPublica;
                
                -- Se não existe, criar
                IF @LigaPaisID IS NULL
                BEGIN
                    SET @LigaPaisID = NEWID();
                    INSERT INTO FantasyChamp.Liga
                        (ID, Nome, Data_Inicio, Data_Fim, ID_tipoLiga, ID_criador, Código_Convite)
                    VALUES
                        (@LigaPaisID, @Pais, GETDATE(), '2026-05-30', 
                         @LigaTipoPublica, @CriadorPadrao, NULL);
                END
                
                -- Adicionar utilizador à Liga do País (se ainda não estiver)
                IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Participa
                              WHERE ID_Utilizador = @UserID AND ID_Liga = @LigaPaisID)
                BEGIN
                    INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
                    VALUES (@UserID, @LigaPaisID);
                END
            END
            
            FETCH NEXT FROM user_cursor INTO @UserID, @Pais;
        END
        
        CLOSE user_cursor;
        DEALLOCATE user_cursor;
        
    END TRY
    BEGIN CATCH
        -- Se houver erro, fechar cursor se ainda aberto
        IF CURSOR_STATUS('local', 'user_cursor') >= 0
        BEGIN
            CLOSE user_cursor;
            DEALLOCATE user_cursor;
        END
        
        -- Não fazer ROLLBACK aqui porque o trigger não deve falhar
        -- O utilizador foi criado, só logamos o erro
        DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
        PRINT 'Erro no trigger trg_Utilizador_CriarLigasPais: ' + @ErrorMsg;
    END CATCH
END;
GO