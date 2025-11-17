import random
import string
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
            FROM FC_Jogador J
            JOIN FC_Posição P ON J.ID_Posição = P.ID;
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
            FROM FC_Jogador J
            JOIN FC_Clube C ON J.ID_clube = C.ID
            JOIN FC_Estado_Jogador E ON J.ID_Estado_Jogador = E.ID
            JOIN FC_Posição P ON J.ID_Posição = P.ID
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




def create(jogador: PlayerDetails):
    id_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO FC_Jogador(
                ID, Nome, ID_Posição, Preço, ID_clube, ID_Estado_Jogador
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            id_str,
            jogador.nome,
            jogador.posicao,  # <- agora isto é o ID da posição
            jogador.preco,
            jogador.Clube_id,
            jogador.id_estado
        )

        cursor.commit()



def update(j_id: str, jogador: PlayerDetails):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE FC_Jogador
            SET Nome = ?,
                ID_Posição = ?,
                Preço = ?,
                ID_clube = ?,
                ID_Estado_Jogador = ?
            WHERE ID = ?;
            """,
            jogador.nome,
            jogador.posicao,
            jogador.preco,
            jogador.Clube_id,
            jogador.id_estado,
            j_id
        )

        cursor.commit()


def delete(j_id: str):
    """
    Apaga um jogador (se não violar integridade referencial).
    """
    with create_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM FC_Jogador WHERE ID = ?;", j_id)
            cursor.commit()
        except IntegrityError as ex:
            # Código genérico de violação FK no SQL Server
            if ex.args[0] == "23000":
                raise Exception(
                    f"Jogador {j_id} não pode ser apagado. "
                    f"Provavelmente está associado a jornadas / equipas."
                ) from ex
