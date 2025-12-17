CREATE PROCEDURE FantasyChamp.JuntarLigaAutomatico
    @ID_Utilizador UNIQUEIDENTIFIER,
    @ID_Liga UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    -- Verificar se já está na liga
    IF NOT EXISTS (SELECT 1 FROM FantasyChamp.Participa
                   WHERE ID_Utilizador = @ID_Utilizador AND ID_Liga = @ID_Liga)
    BEGIN
        -- Inserir
        INSERT INTO FantasyChamp.Participa (ID_Utilizador, ID_Liga)
        VALUES (@ID_Utilizador, @ID_Liga);
    END
END;