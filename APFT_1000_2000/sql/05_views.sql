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

CREATE VIEW FantasyChamp.EstatisticasJogadoresJornada
AS
    SELECT
        PJ.ID_jornada,
        PJ.ID_jogador,
        J.Nome,
        P.Posição AS Posicao,
        J.jogador_imagem,
        C.Nome AS Clube,
        C.ID AS Clube_ID,
        PJ.GolosMarcados,
        PJ.Assistencias,
        PJ.CartoesAmarelos,
        PJ.CartoesVermelhos,
        PJ.TempoJogo,
        PJ.pontuação_total
    FROM FantasyChamp.Pontuação_Jogador PJ
    JOIN FantasyChamp.Jogador J ON PJ.ID_jogador = J.ID
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID;

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

CREATE VIEW FantasyChamp.JogadorCompleto AS
SELECT
    J.ID,
    J.Nome,
    P.Posição AS Posicao,
    J.Preço,
    J.jogador_imagem,
    E.Estado,
    J.ID_Posição,
    J.ID_Estado_Jogador,
    J.ID_clube
FROM FantasyChamp.Jogador J
JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID;

ALTER VIEW FantasyChamp.JogadoresEquipa
AS
    SELECT
        J.ID,
        J.Nome,
        P.Posição AS Posicao,
        J.Preço,
        J.jogador_imagem,
        E.Estado,
        PE.ID_Equipa,
        PE.benched,
        C.Nome AS ClubeNome,
        C.clube_imagem
    FROM FantasyChamp.Jogador J
    JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
    JOIN FantasyChamp.Pertence PE ON J.ID = PE.ID_Jogador  -- INNER JOIN: só jogadores NA equipa
    JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
    JOIN FantasyChamp.Clube C ON J.ID_Clube = C.ID;

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

CREATE VIEW FantasyChamp.PaisView AS
SELECT
    ID,
    nome,
    imagem
FROM FantasyChamp.Pais;

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

CREATE VIEW FantasyChamp.PlayerCompleto AS
SELECT
    J.ID,
    J.Nome,
    P.Posição AS Posicao,
    J.Preço,
    J.jogador_imagem,
    E.Estado,
    C.Nome AS Clube_Nome,
    C.clube_imagem AS Clube_Imagem,
    J.ID_clube,
    J.ID_Posição,
    J.ID_Estado_Jogador
FROM FantasyChamp.Jogador J
JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
LEFT JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID;

CREATE VIEW FantasyChamp.PlayerDetails AS
SELECT
    J.ID,
    J.Nome AS Jogador_Nome,
    P.Posição AS Posicao,
    J.Preço,
    J.jogador_imagem,
    E.Estado,
    C.Nome AS Clube_Nome,
    C.clube_imagem,
    C.ID AS ID_clube,
    PA.nome AS Pais_Clube,
    J.ID_Posição,
    J.ID_Estado_Jogador
FROM FantasyChamp.Jogador J
JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
JOIN FantasyChamp.Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
LEFT JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
LEFT JOIN FantasyChamp.Pais PA ON C.ID_País = PA.ID;

CREATE VIEW FantasyChamp.PontuacaoJogador AS
SELECT
    ID_jogador,
    ID_jornada,
    pontuação_total,
    GolosMarcados,
    Assistencias,
    CartoesAmarelos,
    CartoesVermelhos,
    TempoJogo
FROM FantasyChamp.Pontuação_Jogador;

-- Criar uma view otimizada para consultas frequentes
CREATE VIEW FantasyChamp.vwJogadorPreco
WITH SCHEMABINDING
AS
    SELECT
        ID,
        Preço
    FROM FantasyChamp.Jogador;