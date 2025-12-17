CREATE PROCEDURE FantasyChamp.JuntarLiga
    @ID_Utilizador UNIQUEIDENTIFIER,
    @ID_Liga UNIQUEIDENTIFIER,
    @Codigo VARCHAR(10) = NULL,
    @Resultado BIT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @TipoLiga VARCHAR(16);
    DECLARE @CodigoLiga VARCHAR(10);

    SET @Resultado = 0;

    -- Verificar se já está na liga
    IF EXISTS (SELECT 1 FROM FantasyChamp.Participa
               WHERE ID_Utilizador = @ID_Utilizador AND ID_Liga = @ID_Liga)
    BEGIN
        RETURN;
    END

    -- Obter informações da liga
    SELECT @TipoLiga = ID_tipoLiga, @CodigoLiga = Código_Convite
    FROM FantasyChamp.Liga
    WHERE ID = @ID_Liga;

    IF @TipoLiga IS NULL
    BEGIN
        RETURN;
    END

    -- Verificar se é privada e código está correto
    IF @TipoLiga = 'LT02'  -- privada
    BEGIN
        IF @Codigo IS NULL OR @Codigo != @CodigoLiga
        BEGIN
            RETURN;  -- Código inválido, @Resultado = 0
        END
    END

    -- Inserir
    INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
    VALUES (@ID_Utilizador, @ID_Liga);

    SET @Resultado = 1;  -- Sucesso
END;