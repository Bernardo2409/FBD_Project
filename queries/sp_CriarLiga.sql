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