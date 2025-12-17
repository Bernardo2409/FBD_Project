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