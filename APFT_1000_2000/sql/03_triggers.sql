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
        -- Obter os dados do utilizador inserido
        SELECT @UserID = ID, @Pais = País
        FROM inserted
        WHERE País IS NOT NULL AND LTRIM(RTRIM(País)) != '';

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
        
    END TRY
    BEGIN CATCH
        -- Caso ocorra erro, exibir mensagem
        DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
        PRINT 'Erro' + @ErrorMsg;
    END CATCH
END;
GO
