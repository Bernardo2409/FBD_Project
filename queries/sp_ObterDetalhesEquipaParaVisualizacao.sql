CREATE PROCEDURE FantasyChamp.ObterDetalhesEquipaParaVisualizacao
    @ID_Equipa UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    -- Informações básicas da equipa
    SELECT
        e.ID,
        e.Nome,
        e.Orçamento,
        e.PontuaçãoTotal,
        e.ID_Utilizador,
        CONCAT(u.PrimeiroNome, ' ', u.Apelido) AS Nome_Utilizador,
        -- Estatísticas calculadas
        (SELECT COUNT(*) FROM FantasyChamp.Pertence WHERE ID_Equipa = @ID_Equipa) AS Total_Jogadores,
        (SELECT COUNT(*) FROM FantasyChamp.Pertence WHERE ID_Equipa = @ID_Equipa AND benched = 0) AS Total_Titulares
    FROM FantasyChamp.Equipa e
    LEFT JOIN FantasyChamp.Utilizador u ON e.ID_Utilizador = u.ID
    WHERE e.ID = @ID_Equipa;

    -- Guarda-Redes
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Guarda-Redes'
    ORDER BY p.benched, j.Nome;

    -- Defesas
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Defesa'
    ORDER BY p.benched, j.Nome;

    -- Médios
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Médio'
    ORDER BY p.benched, j.Nome;

    -- Avançados
    SELECT
        j.ID,
        j.Nome,
        j.Preço,
        j.jogador_imagem,
        ej.Estado,
        p.benched,
        c.Nome AS Clube_Nome,
        c.clube_imagem
    FROM FantasyChamp.Jogador j
    JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
    JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
    JOIN FantasyChamp.Estado_Jogador ej ON j.ID_Estado_Jogador = ej.ID
    JOIN FantasyChamp.Clube c ON j.ID_clube = c.ID
    WHERE p.ID_Equipa = @ID_Equipa
      AND pos.Posição = 'Avançado'
    ORDER BY p.benched, j.Nome;

    -- Estatísticas
    SELECT
        -- Contagem por posição
        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Guarda-Redes') AS Total_GR,

        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Defesa') AS Total_Defesas,

        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Médio') AS Total_Medios,

        (SELECT COUNT(*) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Posição pos ON j.ID_Posição = pos.ID
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa AND pos.Posição = 'Avançado') AS Total_Avancados,

        -- Valor total
        (SELECT SUM(j.Preço) FROM FantasyChamp.Jogador j
         JOIN FantasyChamp.Pertence p ON j.ID = p.ID_Jogador
         WHERE p.ID_Equipa = @ID_Equipa) AS Valor_Total_Plantel

END;