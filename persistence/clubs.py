import pyodbc
from persistence.session import create_connection

DEFAULT_IMAGE = "/static/images/Image-not-found.png"

def list_all_clubs():
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT ID,
               Nome,
               Pais_Nome,
               Pais_Imagem,
               clube_imagem
        FROM FantasyChamp.ClubDetails
        ORDER BY Nome
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    clubes = []
    for row in rows:
        imagem_clube = row.clube_imagem if row.clube_imagem else DEFAULT_IMAGE
        imagem_pais = row.Pais_Imagem if row.Pais_Imagem else DEFAULT_IMAGE

        clubes.append({
            "id": row.ID,
            "nome": row.Nome,
            "pais": row.Pais_Nome,
            "pais_imagem": imagem_pais,
            "imagem": imagem_clube
        })

    return clubes



def read_club(club_id):
    conn = create_connection()
    cursor = conn.cursor()

    # ---- info do clube (usando VIEW) ----
    query_club = """
        SELECT ID,
               Nome,
               Pais_Nome,
               Pais_Imagem,
               clube_imagem
        FROM FantasyChamp.ClubDetails
        WHERE ID = ?
    """

    cursor.execute(query_club, club_id)
    row = cursor.fetchone()

    if not row:
        return None

    club_image = row.clube_imagem if row.clube_imagem else DEFAULT_IMAGE
    pais_image = row.Pais_Imagem if row.Pais_Imagem else DEFAULT_IMAGE

    # ---- jogadores deste clube ----
    query_players = """
        SELECT J.ID,
               J.Nome,
               P.Posição AS Posicao,
               J.Preço,
               J.jogador_imagem
        FROM FantasyChamp.Jogador J
        JOIN FantasyChamp.Posição P ON J.ID_Posição = P.ID
        WHERE J.ID_clube = ?
        ORDER BY J.Nome
    """

    cursor.execute(query_players, club_id)
    players_rows = cursor.fetchall()

    jogadores = []
    for p in players_rows:
        jogador_img = p.jogador_imagem if p.jogador_imagem else DEFAULT_IMAGE

        jogadores.append({
            "id": p.ID,
            "nome": p.Nome,
            "posicao": p.Posicao,
            "preco": p.Preço,
            "imagem": jogador_img
        })

    return {
        "id": row.ID,
        "nome": row.Nome,
        "pais": row.Pais_Nome,
        "pais_imagem": pais_image,
        "imagem": club_image,
        "jogadores": jogadores
    }

def list_paginated_clubs(page: int, per_page: int):
    offset = (page - 1) * per_page
    
    with create_connection() as conn:
        cursor = conn.cursor()

        # Total
        cursor.execute("SELECT COUNT(*) FROM FantasyChamp.ClubDetails")
        total = cursor.fetchone()[0]

        # Dados paginados
        cursor.execute("""
            SELECT ID, Nome, Pais_Nome, Pais_Imagem, clube_imagem
            FROM FantasyChamp.ClubDetails
            ORDER BY Nome
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, per_page))
        
        # Processamento com list comprehension
        clubes = [{
            "id": row.ID,
            "nome": row.Nome,
            "pais": row.Pais_Nome,
            "pais_imagem": row.Pais_Imagem or DEFAULT_IMAGE,
            "imagem": row.clube_imagem or DEFAULT_IMAGE
        } for row in cursor.fetchall()]

        return clubes, total