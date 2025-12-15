import pyodbc
from persistence.session import create_connection

DEFAULT_IMAGE = "/static/images/Image-not-found.png"

def list_all_matches():
    """Lista todos os jogos"""
    conn = create_connection()
    cursor = conn.cursor()

    query = """
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
        JOIN FantasyChamp.Clube C2 ON J.ID_Clube2 = C2.ID
        ORDER BY J.Data DESC, Jor.Numero DESC
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    matches = []
    for row in rows:
        imagem_clube1 = row.Clube1_Imagem if row.Clube1_Imagem else DEFAULT_IMAGE
        imagem_clube2 = row.Clube2_Imagem if row.Clube2_Imagem else DEFAULT_IMAGE

        matches.append({
            "id": row.ID,
            "date": row.Data.strftime('%Y-%m-%d') if row.Data else "N/A",
            "round": f"Jornada {row.Jornada}",
            "club1": row.Clube1,
            "club1_image": imagem_clube1,
            "club2": row.Clube2,
            "club2_image": imagem_clube2,
            "goals_home": row.golos_clube1 if row.golos_clube1 is not None else "-",
            "goals_away": row.golos_clube2 if row.golos_clube2 is not None else "-"
        })

    return matches


def read_match(match_id):
    """Obtém detalhes de um jogo específico"""
    conn = create_connection()
    cursor = conn.cursor()

    # Informações do jogo
    query_match = """
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
            J.golos_clube2,
        FROM FantasyChamp.Jogo J
        JOIN FantasyChamp.Jornada Jor ON J.ID_jornada = Jor.ID
        JOIN FantasyChamp.Clube C1 ON J.ID_Clube1 = C1.ID
        JOIN FantasyChamp.Clube C2 ON J.ID_Clube2 = C2.ID
        JOIN FantasyChamp.Pais P1 ON C1.ID_País = P1.ID
        JOIN FantasyChamp.Pais P2 ON C2.ID_País = P2.ID
        WHERE J.ID = ?
    """

    cursor.execute(query_match, match_id)
    row = cursor.fetchone()

    if not row:
        return None

    clube1_image = row.Clube1_Imagem if row.Clube1_Imagem else DEFAULT_IMAGE
    clube2_image = row.Clube2_Imagem if row.Clube2_Imagem else DEFAULT_IMAGE
    clube1_pais_image = row.Clube1_Pais_Imagem if row.Clube1_Pais_Imagem else DEFAULT_IMAGE
    clube2_pais_image = row.Clube2_Pais_Imagem if row.Clube2_Pais_Imagem else DEFAULT_IMAGE

    # Obter estatísticas dos jogadores neste jogo
    query_stats = """
        SELECT 
            J.ID,
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
        JOIN FantasyChamp.Clube C ON J.ID_clube = C.ID
        WHERE PJ.ID_jornada = ? AND PJ.ID_jogo = ?
        ORDER BY C.ID, P.Posição, J.Nome
    """

    cursor.execute(query_stats, row.Jornada_ID, match_id)
    stats_rows = cursor.fetchall()

    jogadores_casa = []
    jogadores_fora = []

    for s in stats_rows:
        jogador_img = s.jogador_imagem if s.jogador_imagem else DEFAULT_IMAGE

        jogador_data = {
            "id": s.ID,
            "nome": s.Nome,
            "posicao": s.Posicao,
            "imagem": jogador_img,
            "clube": s.Clube,
            "golos": s.GolosMarcados if s.GolosMarcados is not None else 0,
            "assistencias": s.Assistencias if s.Assistencias is not None else 0,
            "amarelos": s.CartoesAmarelos if s.CartoesAmarelos is not None else 0,
            "vermelhos": s.CartoesVermelhos if s.CartoesVermelhos is not None else 0,
            "minutos": s.TempoJogo if s.TempoJogo is not None else 0,
            "pontuacao": s.pontuação_total if s.pontuação_total is not None else 0
        }

        if s.Clube_ID == row.Clube1_ID:
            jogadores_casa.append(jogador_data)
        else:
            jogadores_fora.append(jogador_data)

    return {
        "id": row.ID,
        "data": row.Data.strftime('%d/%m/%Y') if row.Data else "N/A",
        "jornada": f"Jornada {row.Jornada}",
        "jornada_numero": row.Jornada,
        "clube1": {
            "id": row.Clube1_ID,
            "nome": row.Clube1,
            "imagem": clube1_image,
            "pais": row.Clube1_Pais,
            "pais_imagem": clube1_pais_image
        },
        "clube2": {
            "id": row.Clube2_ID,
            "nome": row.Clube2,
            "imagem": clube2_image,
            "pais": row.Clube2_Pais,
            "pais_imagem": clube2_pais_image
        },
        "golos_casa": row.golos_clube1 if row.golos_clube1 is not None else 0,
        "golos_fora": row.golos_clube2 if row.golos_clube2 is not None else 0,
        "jogadores_casa": jogadores_casa,
        "jogadores_fora": jogadores_fora
    }


def list_paginated_matches(page: int, per_page: int):
    """Lista jogos com paginação"""
    offset = (page - 1) * per_page

    conn = create_connection()
    cursor = conn.cursor()

    # Total de jogos
    cursor.execute("SELECT COUNT(*) FROM FantasyChamp.Jogo;")
    total = cursor.fetchone()[0]

    # Query paginada
    query = f"""
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
        JOIN FantasyChamp.Clube C2 ON J.ID_Clube2 = C2.ID
        ORDER BY J.Data DESC, Jor.Numero DESC
        OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY;
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    matches = []
    for row in rows:
        imagem_clube1 = row.Clube1_Imagem if row.Clube1_Imagem else DEFAULT_IMAGE
        imagem_clube2 = row.Clube2_Imagem if row.Clube2_Imagem else DEFAULT_IMAGE

        matches.append({
            "id": row.ID,
            "date": row.Data.strftime('%Y-%m-%d') if row.Data else "N/A",
            "round": f"Jornada {row.Jornada}",
            "club1": row.Clube1,
            "club1_image": imagem_clube1,
            "club2": row.Clube2,
            "club2_image": imagem_clube2,
            "goals_home": row.golos_clube1 if row.golos_clube1 is not None else "-",
            "goals_away": row.golos_clube2 if row.golos_clube2 is not None else "-"
        })

    return matches, total