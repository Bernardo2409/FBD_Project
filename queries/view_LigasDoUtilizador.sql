CREATE VIEW FantasyChamp.LigasDoUtilizador
AS
    SELECT
        L.ID,
        L.Nome,
        L.Data_Inicio,
        L.Data_Fim,
        L.ID_tipoLiga,
        L.ID_criador,
        L.Código_Convite,
        P.ID_Utilizador
    FROM FantasyChamp.Liga L
    JOIN FantasyChamp.Participa P ON L.ID = P.ID_Liga;