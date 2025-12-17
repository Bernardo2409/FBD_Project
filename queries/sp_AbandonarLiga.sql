CREATE PROCEDURE FantasyChamp.AbandonarLiga
    @ID_Utilizador UNIQUEIDENTIFIER,
    @ID_Liga UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    DELETE FROM FantasyChamp.Participa
    WHERE ID_Utilizador = @ID_Utilizador
      AND ID_Liga = @ID_Liga;
END;