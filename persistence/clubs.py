import pyodbc
from persistence.session import create_connection

DEFAULT_IMAGE = "/static/images/Image-not-found.png"

def list_all_clubs():
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT ID, Nome, País, clube_imagem
        FROM FC_Clube
        ORDER BY Nome
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    clubes = []
    for row in rows:
        imagem = row.clube_imagem if row.clube_imagem else DEFAULT_IMAGE

        clubes.append({
            "id": row.ID,
            "nome": row.Nome,
            "pais": row.País,
            "imagem": imagem
        })

    return clubes


def read_club(club_id):
    conn = create_connection()
    cursor = conn.cursor()

    # ---- info do clube ----
    query_club = """
        SELECT ID, Nome, País, clube_imagem
        FROM FC_Clube
        WHERE ID = ?
    """

    cursor.execute(query_club, club_id)
    row = cursor.fetchone()

    if not row:
        return None

    club_image = row.clube_imagem if row.clube_imagem else DEFAULT_IMAGE

    # ---- jogadores deste clube ----
    query_players = """
        SELECT ID, Nome, Posição, Preço, jogador_imagem
        FROM FC_Jogador
        WHERE ID_clube = ?
        ORDER BY Nome
    """

    cursor.execute(query_players, club_id)
    players_rows = cursor.fetchall()

    jogadores = []
    for p in players_rows:
        jogador_img = p.jogador_imagem if p.jogador_imagem else DEFAULT_IMAGE

        jogadores.append({
            "id": p.ID,
            "nome": p.Nome,
            "posicao": p.Posição,
            "preco": p.Preço,
            "imagem": jogador_img
        })

    return {
        "id": row.ID,
        "nome": row.Nome,
        "pais": row.País,
        "imagem": club_image,
        "jogadores": jogadores
    }
