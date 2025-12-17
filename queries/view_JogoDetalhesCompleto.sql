CREATE VIEW FantasyChamp.JogoDetalhesCompleto
AS
    SELECT
        J.ID,
        J.Data,
        Jor.Numero AS Jornada,
        Jor.ID AS Jornada_ID,
        C1.ID AS Clube1_ID,
        C1.Nome AS Clube1,
        C1.clube_imagem AS Clube1_Imagem,
        P1.nome AS Clube1_Pais,
        P1.imagem AS Clube1_Pais_Imagem,
        C2.ID AS Clube2_ID,
        C2.Nome AS Clube2,
        C2.clube_imagem AS Clube2_Imagem,
        P2.nome AS Clube2_Pais,
        P2.imagem AS Clube2_Pais_Imagem,
        J.golos_clube1,
        J.golos_clube2
    FROM FantasyChamp.Jogo J
    JOIN FantasyChamp.Jornada Jor ON J.ID_jornada = Jor.ID
    JOIN FantasyChamp.Clube C1 ON J.ID_Clube1 = C1.ID
    JOIN FantasyChamp.Clube C2 ON J.ID_Clube2 = C2.ID
    JOIN FantasyChamp.Pais P1 ON C1.ID_País = P1.ID
    JOIN FantasyChamp.Pais P2 ON C2.ID_País = P2.ID;