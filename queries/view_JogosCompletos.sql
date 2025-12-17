CREATE VIEW FantasyChamp.JogosCompletos
AS
    SELECT
        J.ID,
        J.Data,
        Jor.Numero AS Jornada,
        C1.Nome AS Clube1,
        C1.clube_imagem AS Clube1_Imagem,
        C2.Nome AS Clube2,
        C2.clube_imagem AS Clube2_Imagem,
        J.golos_clube1,
        J.golos_clube2
    FROM FantasyChamp.Jogo J
    JOIN FantasyChamp.Jornada Jor ON J.ID_jornada = Jor.ID
    JOIN FantasyChamp.Clube C1 ON J.ID_Clube1 = C1.ID
    JOIN FantasyChamp.Clube C2 ON J.ID_Clube2 = C2.ID;