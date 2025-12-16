CREATE VIEW FantasyChamp.EquipaCompleta
AS
    SELECT
        e.ID,
        e.Nome,
        e.Orçamento,
        e.PontuaçãoTotal,
        e.ID_Utilizador,
        
        COUNT(je.ID_Jogador) as Num_Jogadores,
        SUM(j.Preço) as Valor_Total_Plantel
    FROM FantasyChamp.Equipa e
    LEFT JOIN FantasyChamp.Pertence je ON e.ID = je.ID_Equipa
    LEFT JOIN FantasyChamp.Jogador j ON je.ID_Jogador = j.ID
    GROUP BY e.ID, e.Nome, e.Orçamento, e.PontuaçãoTotal, e.ID_Utilizador;