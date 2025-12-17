CREATE VIEW FantasyChamp.ParticipantesLiga
AS
    SELECT
        P.ID_Liga,
        U.PrimeiroNome + ' ' + U.Apelido AS nome,
        E.Nome AS equipa,
        E.ID AS id_equipa,
        U.ID AS id_utilizador
    FROM FantasyChamp.Participa P
    JOIN FantasyChamp.Utilizador U ON P.ID_Utilizador = U.ID
    LEFT JOIN FantasyChamp.Equipa E ON U.ID = E.ID_utilizador;