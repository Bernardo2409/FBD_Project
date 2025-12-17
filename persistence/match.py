import pyodbc
from persistence.session import create_connection

DEFAULT_IMAGE = "/static/images/Image-not-found.png"

def list_all_matches():
    with create_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM FantasyChamp.JogosCompletos
            ORDER BY Data DESC, Jornada DESC
        """)
        
        matches = []
        for row in cursor:
            imagem_clube1 = row.Clube1_Imagem if row.Clube1_Imagem else DEFAULT_IMAGE
            imagem_clube2 = row.Clube2_Imagem if row.Clube2_Imagem else DEFAULT_IMAGE
            
            matches.append({
                "id": row.ID,
                "date": row.Data.strftime('%Y-%m-%d') if row.Data else "N/A",
                "round": f"Round {row.Jornada}",
                "club1": row.Clube1,
                "club1_image": imagem_clube1,
                "club2": row.Clube2,
                "club2_image": imagem_clube2,
                "goals_home": row.golos_clube1 if row.golos_clube1 is not None else "-",
                "goals_away": row.golos_clube2 if row.golos_clube2 is not None else "-"
            })
        
        return matches


def read_match(match_id):
    with create_connection() as conn:
        cursor = conn.cursor()

        # 1. Informações do jogo - usando view
        cursor.execute("""
            SELECT * FROM FantasyChamp.JogoDetalhesCompleto
            WHERE ID = ?
        """, match_id)

        row = cursor.fetchone()

        if not row:
            return None

        clube1_image = row.Clube1_Imagem if row.Clube1_Imagem else DEFAULT_IMAGE
        clube2_image = row.Clube2_Imagem if row.Clube2_Imagem else DEFAULT_IMAGE
        clube1_pais_image = row.Clube1_Pais_Imagem if row.Clube1_Pais_Imagem else DEFAULT_IMAGE
        clube2_pais_image = row.Clube2_Pais_Imagem if row.Clube2_Pais_Imagem else DEFAULT_IMAGE

        # 2. Obter estatísticas dos jogadores - usando view
        cursor.execute("""
            SELECT * FROM FantasyChamp.EstatisticasJogadoresJornada
            WHERE ID_jornada = ? 
              AND Clube_ID IN (?, ?)
              AND TempoJogo > 0
            ORDER BY Clube_ID, Posicao, Nome
        """, row.Jornada_ID, row.Clube1_ID, row.Clube2_ID)

        stats_rows = cursor.fetchall()

        jogadores_casa = []
        jogadores_fora = []

        for s in stats_rows:
            jogador_img = s.jogador_imagem if s.jogador_imagem else DEFAULT_IMAGE

            jogador_data = {
                "id": s.ID_jogador,
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
            "jornada": f"Round {row.Jornada}",
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

    offset = (page - 1) * per_page

    with create_connection() as conn:
        cursor = conn.cursor()

        # Total de jogos (pode usar view também)
        cursor.execute("SELECT COUNT(*) FROM FantasyChamp.JogosCompletos")
        total = cursor.fetchone()[0]

        # Query paginada usando view
        query = f"""
            SELECT *
            FROM FantasyChamp.JogosCompletos
            ORDER BY Data DESC, Jornada DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
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
                "round": f"Round {row.Jornada}",
                "club1": row.Clube1,
                "club1_image": imagem_clube1,
                "club2": row.Clube2,
                "club2_image": imagem_clube2,
                "goals_home": row.golos_clube1 if row.golos_clube1 is not None else "-",
                "goals_away": row.golos_clube2 if row.golos_clube2 is not None else "-"
            })

        return matches, total