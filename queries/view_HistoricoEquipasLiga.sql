CREATE VIEW FantasyChamp.HistoricoEquipasLiga AS
SELECT
    P.ID_Liga,
    PE.ID_Equipa,
    PE.ID_jornada,
    PE.pontuação_jornada,
    PE.pontuação_acumulada
FROM FantasyChamp.Pontuação_Equipa PE
JOIN FantasyChamp.Equipa E ON PE.ID_Equipa = E.ID
JOIN FantasyChamp.Participa P ON E.ID_Utilizador = P.ID_Utilizador;