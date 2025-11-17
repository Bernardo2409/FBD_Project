from typing import NamedTuple

from pyodbc import IntegrityError
from persistence.session import create_connection


# --- DATA MODELS ---

class PlayerDescriptor(NamedTuple):
    id: str
    nome: str
    posicao: str
    preco: float
    jogador_imagem: str


class PlayerDetails(NamedTuple):
    id: str
    nome: str
    posicao: str
    preco: float
    nome_clube: str
    id_estado: str
    Clube_id: str
    clube_imagem: str
    jogador_imagem: str


# --- CRUD FUNCTIONS ---

def list_all() -> list[PlayerDescriptor]:
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT J.ID, J.Nome, P.Posição AS Posicao, J.Preço, J.jogador_imagem
            FROM FantasyChamp.FC_Jogador J
            JOIN FantasyChamp.FC_Posição P ON J.ID_Posição = P.ID;
        """)

        return list(map(
            lambda row:
                PlayerDescriptor(
                    row.ID,
                    row.Nome,
                    row.Posicao,
                    row.Preço,
                    row.jogador_imagem if row.jogador_imagem
                    else '/static/images/Image-not-found.png'
                ),
            cursor
        ))



def read(j_id: str):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                J.ID, 
                J.Nome, 
                P.Posição AS Posicao,
                J.Preço,
                J.jogador_imagem,
                C.Nome AS Clube,
                C.clube_imagem,
                C.ID AS Clube_id,
                E.Estado
            FROM FantasyChamp.FC_Jogador J
            JOIN FantasyChamp.FC_Clube C ON J.ID_clube = C.ID
            JOIN FantasyChamp.FC_Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
            JOIN FantasyChamp.FC_Posição P ON J.ID_Posição = P.ID
            WHERE J.ID = ?;
        """, j_id)

        row = cursor.fetchone()
        if not row:
            return None

        return PlayerDetails(
            row.ID,
            row.Nome,
            row.Posicao,
            row.Preço,
            row.Clube,
            row.Estado,
            row.Clube_id,
            row.clube_imagem if row.clube_imagem else '/static/images/Image-not-found.png',
            row.jogador_imagem if row.jogador_imagem else '/static/images/Image-not-found.png'
        )