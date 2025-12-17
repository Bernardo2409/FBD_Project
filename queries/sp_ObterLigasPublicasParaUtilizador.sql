CREATE PROCEDURE FantasyChamp.ObterLigasPublicasParaUtilizador
    @PaisUser NVARCHAR(50),
    @ID_User UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        L.ID,
        L.Nome,
        L.Data_Inicio,
        L.Data_Fim,
        L.ID_tipoLiga,
        L.ID_criador,
        L.Código_Convite,
        U.PrimeiroNome
    FROM FantasyChamp.Liga L
    JOIN FantasyChamp.Utilizador U ON L.ID_criador = U.ID
    WHERE
        L.ID_tipoLiga = 'LT01'
        AND L.Data_Fim > GETDATE()
        AND L.Nome IN ('Mundial', @PaisUser)
        AND L.ID NOT IN (
            SELECT ID_Liga FROM FantasyChamp.Participa
            WHERE ID_Utilizador = @ID_User
        )
    ORDER BY L.Nome;
END;