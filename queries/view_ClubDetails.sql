CREATE VIEW FantasyChamp.ClubDetails AS
SELECT
    C.ID,
    C.Nome,
    P.nome AS Pais_Nome,
    P.imagem AS Pais_Imagem,
    C.clube_imagem,
    C.ID_País
FROM FantasyChamp.Clube C
JOIN FantasyChamp.Pais P ON C.ID_País = P.ID;