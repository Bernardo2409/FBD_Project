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