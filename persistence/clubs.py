import pyodbc
from persistence.session import create_connection

DEFAULT_IMAGE = "/static/images/Image-not-found.png"

def list_all_clubs():
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT C.ID,
               C.Nome,
               P.País AS Pais_Nome,
               P.país_imagem AS Pais_Imagem,
               C.clube_imagem
        FROM FantasyChamp.FC_Clube C
        JOIN FantasyChamp.FC_País P ON C.ID_Pais = P.ID
        ORDER BY C.Nome
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

    # ---- info do clube ----
    query_club = """
        SELECT C.ID,
               C.Nome,
               P.País AS Pais_Nome,
               P.país_imagem AS Pais_Imagem,
               C.clube_imagem
        FROM FantasyChamp.FC_Clube C
        JOIN FantasyChamp.FC_País P ON C.ID_Pais = P.ID
        WHERE C.ID = ?
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
        FROM FantasyChamp.FC_Jogador J
        JOIN FantasyChamp.FC_Posição P ON J.ID_Posição = P.ID
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
