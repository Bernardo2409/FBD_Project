CREATE VIEW FantasyChamp.ContagemEquipa
AS
    SELECT
        PE.ID_Equipa,
        SUM(CASE WHEN P.Posição = 'Goalkeeper' THEN 1 ELSE 0 END) as gr,
        SUM(CASE WHEN P.Posição = 'Defender' THEN 1 ELSE 0 END) as defesa,
        SUM(CASE WHEN P.Posição = 'Midfielder' THEN 1 ELSE 0 END) as medio,
        SUM(CASE WHEN P.Posição = 'Forward' THEN 1 ELSE 0 END) as avancado,
        COUNT(*) as total
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador
    GROUP BY PE.ID_Equipa;