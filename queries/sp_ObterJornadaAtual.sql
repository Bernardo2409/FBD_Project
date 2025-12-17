CREATE PROCEDURE FantasyChamp.ObterJornadaAtual
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @JornadaID VARCHAR(16);
    DECLARE @Numero INT;

    SELECT TOP 1
        @JornadaID = ID,
        @Numero = Numero
    FROM FantasyChamp.Jornada
    WHERE GETDATE() BETWEEN Data_Inicio AND Data_Fim
    ORDER BY Numero;

    IF @JornadaID IS NULL
    BEGIN
        SELECT TOP 1
            @JornadaID = ID,
            @Numero = Numero
        FROM FantasyChamp.Jornada
        ORDER BY Numero DESC;
    END

    SELECT
        @JornadaID as ID,
        @Numero as Numero;
END;