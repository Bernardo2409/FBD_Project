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